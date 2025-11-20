import os
import math
import numpy as np
import pandas as pd

# ==== ユーザーが調整できるパラメータ ====
PER_SOURCE_MIN_PCT = 5.0        # 各取水源の最小寄与割合（例: 5.0 %）
MIN_GRADIENT_M_PER_KM   = 0.01   # 最低勾配（m/km）
# ======================================

def main():
    # datadir
    h08dir = '/your/work/directory'
    os.makedirs(h08dir, exist_ok=True)

    # ---- inputs (global 2160 x 4320, float32) ----
    mask_path   = f'{h08dir}/city_clrd0000.gl5'
    mask        = np.fromfile(mask_path, dtype='float32').reshape(2160, 4320)

    rivnxl_path = f"{h08dir}/rivnxl.CAMA.gl5"
    rivnxl_gl5  = np.fromfile(rivnxl_path, dtype='float32').reshape(2160, 4320)

    rivout_path = f'{h08dir}/W5E5LR__00000000.gl5'
    rivout      = np.fromfile(rivout_path, dtype='float32').reshape(2160, 4320)

    rivnum_path = f'{h08dir}/rivnum.CAMA.gl5'
    rivnum      = np.fromfile(rivnum_path, dtype='float32').reshape(2160, 4320)

    poptot_path = f'{h08dir}/GPW4ag__20100000.gl5'
    poptot      = np.fromfile(poptot_path, dtype='float32').reshape(2160, 4320)

    rivara_path = f'{h08dir}/rivara.CAMA.gl5'
    rivara      = np.fromfile(rivara_path, dtype='float32').reshape(2160, 4320)

    elv_path    = f'{h08dir}/elevtn.CAMA.gl5'
    elv         = np.fromfile(elv_path, dtype='float32').reshape(2160, 4320)


    prf_path    = f"{h08dir}/prf_clrd0000.gl5"
    prf         = np.fromfile(prf_path, dtype='float32').reshape(2160, 4320)

    # camacity dataset
    text_path = f'{h08dir}/camacity_fifth.txt'
    df = pd.read_csv(text_path, sep="|", header=None)
    df.columns = [
        'city_code', 'pop_rank', 'status', 'type', 'latitude', 'longitude', 'city_name', 'wup_pop',
        '5region_code', '5region_name', '17region_code', '17region_name', '22region_code', '22region_name',
        'country_code', 'country_name', 'full_pop', 'clustered_pop', 'grid_count', 'administrative_level',
        'inputunit_count', 'Mcdonald2014', 'mainriver_count', 'aqueduct_distance', 'landuse_precision',
    ]

    # 出力先
    out_dir = f'{h08dir}/aqd_dat_'
    os.makedirs(out_dir, exist_ok=True)

    for city_num in range(1, 1861):
        # スキップ条件
        if df.loc[city_num - 1, 'status'] == 'RMVD' or df.loc[city_num - 1, 'type'] == 'NoMK':
            continue

        # ---- 切り出し範囲 ----
        left, right, bottom, top = get_citycenter(city_num, df, buffer=5.0)
        upperindex, lowerindex, leftindex, rightindex, _, _ = geography(left, right, bottom, top)

        # ---- 切り出し配列 ----
        mask_cropped   = mask[upperindex:lowerindex, leftindex:rightindex]
        mask_cropped   = np.where(mask_cropped == city_num, 1, 0).astype(np.int8)

        riv_nxtxy_crop = nxtl2nxtxy(rivnxl_gl5, upperindex, lowerindex, leftindex, rightindex)
        rivout_cropped = rivout[upperindex:lowerindex, leftindex:rightindex] * 60 * 60 * 24 * 365 / 1000.0  # m3/yr
        rivnum_cropped = rivnum[upperindex:lowerindex, leftindex:rightindex]
        poptot_cropped = poptot[upperindex:lowerindex, leftindex:rightindex]
        elv_cropped    = elv[upperindex:lowerindex, leftindex:rightindex]
        prf_cropped    = prf[upperindex:lowerindex, leftindex:rightindex]

        # 都市人口
        city_pop = float(np.sum(poptot_cropped[mask_cropped == 1]))

        # inlet 座標（ローカル座標）
        prf_coords = np.where(prf_cropped == city_num)

        # ---- 候補探索（100km & サイズ>=5流域 & 標高条件 & 都市外、降順で交差スキップ）----
        source_list = explore_flow(
            mask_cropped=mask_cropped,
            rivnum_cropped=rivnum_cropped,
            rivout_cropped=rivout_cropped,
            riv_nxtxy_cropped=riv_nxtxy_crop,
            elv_cropped=elv_cropped,
            inlet_coords=prf_coords,
            top=top,
            left=left,
            min_basin_size=5,
            search_radius_km=100,
            sort_by_flow=True
        )

        # ==== 追加1: inlet 自身の座標を除外 ====
        inlet_set = set(zip(prf_coords[0], prf_coords[1]))
        source_list = [rc for rc in source_list if rc not in inlet_set]

        # ==== 追加2: 取水可能量で降順ソートし、閾値以下を除外 ====
        contrib_pairs = []  # [( (y,x), value ), ...]
        for rc in source_list:
            y, x = rc
            m3yr = rivout_cropped[y, x]  # m3/yr
            contrib_pairs.append((rc, m3yr))
        contrib_pairs.sort(key=lambda t: t[1], reverse=True)
        total_val = sum(v for _, v in contrib_pairs)
        per_cut = (PER_SOURCE_MIN_PCT / 100.0) * total_val
        contrib_pairs = [t for t in contrib_pairs if t[1] >= per_cut]

        # フィルタ後の source_list（座標のみ）
        source_list = [t[0] for t in contrib_pairs]

        # ---- 出力（global 2160x4320 に city_num を配置して保存）----
        out_arr = np.zeros((2160, 4320), dtype=np.float32)
        for (yy, xx) in source_list:
            gy = upperindex + yy
            gx = leftindex + xx
            if 0 <= gy < 2160 and 0 <= gx < 4320:
                out_arr[gy, gx] = float(city_num)

        out_path = os.path.join(out_dir, f'unlm_aqd_{city_num:08}.gl5')
        out_arr.tofile(out_path)
        print(f"Saved: {out_path}")


def get_citycenter(city_num, df, buffer=5.0):
    # df は既に読み込んであるのでそのまま利用
    if city_num < 1 or city_num > len(df):
        raise ValueError(f"Invalid city_num: {city_num}. It should be between 1 and {len(df)}.")
    longitude = float(df.loc[city_num - 1, 'longitude'])
    latitude  = float(df.loc[city_num - 1, 'latitude'])
    left   = int(longitude - buffer)
    right  = int(longitude + buffer)
    bottom = int(latitude  - buffer)
    top    = int(latitude  + buffer)
    return left, right, bottom, top


def geography(left, right, bottom, top, resolution=12):
    upperindex = int((90  - top)    * resolution)
    lowerindex = int((90  - bottom) * resolution)
    leftindex  = int((180 + left)   * resolution)
    rightindex = int((180 + right)  * resolution)
    rgnshape   = (lowerindex - upperindex, rightindex - leftindex)
    img_extent = (left, right, bottom, top)
    return upperindex, lowerindex, leftindex, rightindex, rgnshape, img_extent


def nxtl2nxtxy(rivnxl, upperindex, lowerindex, leftindex, rightindex,
               a=2160, b=4320, nan_value = 1e20):
    # region
    rivnxl_cropped = rivnxl[upperindex:lowerindex, leftindex:rightindex]
    H, W = rivnxl_cropped.shape
    rivnxl_cropped[rivnxl_cropped < 10] = np.nan

    # L -> (y, x)
    mask = ~np.isnan(rivnxl_cropped)
    riv_flat = rivnxl_cropped[mask].astype(int)
    lat_l = (riv_flat - 1)  // b
    lon_l = (riv_flat - 1) %  b
    lat_l = lat_l.astype(float)
    lon_l = lon_l.astype(float)

    # offset
    lat_l -= upperindex
    lon_l -= leftindex

    # 範囲外のセルをNaNにする
    out_of_bounds_mask = (lat_l < 0) | (lat_l >= H) | (lon_l < 0) | (lon_l >= W)
    lat_l[out_of_bounds_mask] = nan_value
    lon_l[out_of_bounds_mask] = nan_value

    # (y, x)座標ペアとして格納
    riv_nxtxy_cropped  = np.full((*rivnxl_cropped.shape, 2), np.nan, dtype=float)
    riv_nxtxy_cropped[mask] = np.column_stack((lat_l, lon_l))

    # 既存の実装では int キャストを行っているため踏襲（無効値1e20がintに溢れる可能性あり）
    # 警告抑制を重視するなら astype(int) を外し、float NaN のまま扱うのが安全。
    return riv_nxtxy_cropped.astype(int)


def xy2lonlat(y, x, top=90, left=-180, lat_num=2160, lon_num=4320):
    if 0 <= x <= lon_num:
        latcnt = top - y*(180/lat_num)
        loncnt = left + x*(360/lon_num)
    else:
        loncnt = 1e20
        latcnt = 1e20
    return latcnt, loncnt


def lonlat_distance(lat_a, lon_a, lat_b, lon_b):
    """ Hybeny's Distance Formula """
    pole_radius = 6356752.314245
    equator_radius = 6378137.0
    radlat_a = math.radians(lat_a)
    radlon_a = math.radians(lon_a)
    radlat_b = math.radians(lat_b)
    radlon_b = math.radians(lon_b)

    lat_dif = radlat_a - radlat_b
    lon_dif = radlon_a - radlon_b
    lat_ave = (radlat_a + radlat_b) / 2

    e2 = (math.pow(equator_radius, 2) - math.pow(pole_radius, 2)) \
            / math.pow(equator_radius, 2)

    w = math.sqrt(1 - e2 * math.pow(math.sin(lat_ave), 2))

    m = equator_radius * (1 - e2) / math.pow(w, 3)

    n = equator_radius / w

    distance = math.sqrt(math.pow(m * lat_dif, 2) \
                + math.pow(n * lon_dif * math.cos(lat_ave), 2))

    return distance / 1000


def create_radius_mask(city_cropped, inlet_coords, elv_cropped,
                       top, left, search_radius_km=100):
    """
    PRF(浄水場)から search_radius_km 以内のグリッドを True にした探索マスクと、
    各グリッドセルに対する
        - 最も近い PRF の標高 (nearest_prf_elv)
        - 最も近い PRF までの距離 [km] (nearest_prf_dist)
    を返す。

    inlet_coords: np.where(prf_cropped == city_num) で得られる (y_idx_array, x_idx_array)
    """
    H, W = city_cropped.shape
    radius_mask      = np.zeros((H, W), dtype=bool)
    nearest_prf_elv  = np.full((H, W), np.nan, dtype=float)
    nearest_prf_dist = np.full((H, W), np.nan, dtype=float)

    # 1) 基準点（PRF or 都市マスク）リスト
    if inlet_coords[0].size > 0 and inlet_coords[1].size > 0:
        # PRF がある場合 → PRF 座標を基準にする
        centers = list(zip(inlet_coords[0], inlet_coords[1]))
    else:
        # PRF が無い場合 → 都市マスク上のセルを基準にする（フォールバック）
        city_indices = np.where(city_cropped == 1)
        centers = list(zip(city_indices[0], city_indices[1]))

    # 2) 各セルについて「最近傍 PRFの距離」と「そのPRFの標高」を計算
    for yy in range(H):
        for xx in range(W):
            lat_b, lon_b = xy2lonlat(yy, xx, top, left)

            d_min  = float('inf')
            elv_min = np.nan

            for cy, cx in centers:
                lat_a, lon_a = xy2lonlat(cy, cx, top, left)
                d = lonlat_distance(lat_a, lon_a, lat_b, lon_b)  # [km]

                if d < d_min:
                    d_min  = d
                    elv_min = elv_cropped[cy, cx]

            # 半径 search_radius_km 以内ならマスクをON
            if d_min <= search_radius_km:
                radius_mask[yy, xx]      = True
                nearest_prf_elv[yy, xx]  = elv_min
                nearest_prf_dist[yy, xx] = d_min

    return radius_mask, nearest_prf_elv, nearest_prf_dist


def get_downstream_coords(start_coord, riv_nxtxy_cropped):
    """
    指定した座標の下流にある座標を探索
    """
    visited_coords = set()
    target_coord = start_coord

    while target_coord not in visited_coords:
        visited_coords.add(target_coord)
        target_row, target_col = target_coord

        # ① インデックスが有効範囲内かチェック
        if target_row < 0 or target_row >= riv_nxtxy_cropped.shape[0] or \
           target_col < 0 or target_col >= riv_nxtxy_cropped.shape[1]:
            print(f"Warning: target_row={target_row}, target_col={target_col} is out of bounds!")
            break  # ループを終了

        # ② 無効な値 (NaN) をチェック
        if np.isnan(target_row) or np.isnan(target_col):
            print("Warning: target_row or target_col is NaN")
            break

        # ③ 次の座標を取得
        next_coord = riv_nxtxy_cropped[target_row, target_col]

        # ④ 次の座標が空なら終了
        if next_coord.size == 0 or next_coord.shape != (2,):
            break

        target_coord = tuple(next_coord)  # NumPy配列をタプルに変換

    return visited_coords


def explore_flow(mask_cropped, rivnum_cropped, rivout_cropped, riv_nxtxy_cropped,
                 elv_cropped, inlet_coords, top, left,
                 min_basin_size=5, 
                 search_radius_km=100, 
                 sort_by_flow=True):
    """
    100km以内の「サイズ>=min_basin_size」の流域セルをすべて候補にし、
    流量降順で走査。候補セルの下流系列が既存sourceと交差すればスキップ。
    しきい値判定は行わず、最後まで選別する。
    """
    # --- 1) 半径マスク ＋ 最近傍PRFの標高・距離 ---
    search_mask, nearest_prf_elv, nearest_prf_dist = create_radius_mask(
        city_cropped=mask_cropped,
        inlet_coords=inlet_coords,
        elv_cropped=elv_cropped,
        top=top,
        left=left,
        search_radius_km=search_radius_km
    )

    # --- 2) 流域サイズフィルタ（サイズ>=min_basin_size）---
    rivnum_local = rivnum_cropped.copy()
    rivnum_local[rivnum_local <= 0] = np.nan
    uniq, cnt = np.unique(rivnum_local[~np.isnan(rivnum_local)], return_counts=True)
    large_basins = set(uniq[cnt >= min_basin_size].astype(int))
    basin_ok_mask = np.isin(rivnum_cropped.astype(int), list(large_basins))

    # --- 3) 勾配フィルタ（自然導水のための最低勾配）---
    # head = elv_cell - elv_prf  [m]
    # dist = 最近傍PRFまでの距離 [km]
    # grad = head / dist         [m/km]
    head = elv_cropped - nearest_prf_elv
    # ゼロ除算防止 & dist が NaN / 0 のところは非採用
    dist_safe = np.where(nearest_prf_dist > 0, nearest_prf_dist, np.nan)
    grad = head / dist_safe  # m/km

    # 勾配条件：
    #  - head > 0（PRFより高い）
    #  - grad >= MIN_GRADIENT_M_PER_KM
    elev_ok_mask = head > 0
    grad_ok_mask = grad >= MIN_GRADIENT_M_PER_KM

    # 都市外 & 半径内 & 流域サイズOK & 勾配OK
    candidate_mask = search_mask & basin_ok_mask & (mask_cropped == 0) & elev_ok_mask & grad_ok_mask

    # --- 4) 初期source（inlet）---
    source_list = list(zip(inlet_coords[0], inlet_coords[1]))
    source_set  = set(source_list)

    # --- 5) 候補列挙＆降順ソート ---
    cand_y, cand_x = np.where(candidate_mask)
    candidates = list(zip(cand_y, cand_x))
    if sort_by_flow and candidates:
        candidates.sort(key=lambda rc: rivout_cropped[rc[0], rc[1]], reverse=True)

    # --- 6) 下流系列キャッシュとブロック集合 ---
    downstream_cache: dict[tuple, set] = {}
    blocked_set: set = set()   # 交差でスキップと判定済み系列の全座標

    # --- 7) 採択ループ ---
    for rc in candidates:
        if rc in source_set or rc in blocked_set:
            continue

        # 下流系列をメモ化して取得
        if rc in downstream_cache:
            ds = downstream_cache[rc]
        else:
            ds = get_downstream_coords(rc, riv_nxtxy_cropped)
            downstream_cache[rc] = ds

        # 既存sourceと交差するならスキップ（系列全体をblockedに）
        if source_set.intersection(ds):
            blocked_set.update(ds)
            continue

        # 採択
        source_list.append(rc)
        source_set.add(rc)

    return source_list


if __name__ == '__main__':
    main()
