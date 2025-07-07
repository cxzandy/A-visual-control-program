import open3d as o3d
import numpy as np
import random

class Model:
    def __init__(self):
        self.point = np.array([0, 0, 0])
        self.direction = np.array([0, 0, 1])
        self.r = 0
        self.lIndices = []
        self.gIndices = []

def RANSAC_FIT_Cylinder(pcd, sigma, min_r, max_r, sample_num, iter):
    """
    :param pcd: open3d点云对象
    :param sigma: 距离拟合圆柱两侧的距离
    :param min_r: 圆柱最小半径
    :param max_r: 圆柱最大半径
    :param sample_num: 随机采样的点数
    :param iter: 迭代次数
    :return: 圆柱中心点、方向、半径
    """
    k = 50  # 邻近点数，计算法向量
    if not pcd.has_normals():
        pcd.estimate_normals(o3d.geometry.KDTreeSearchParamKNN(k))
    pcd.orient_normals_consistent_tangent_plane(10)
    points = np.asarray(pcd.points)
    normals = np.asarray(pcd.normals)
    nums = points.shape[0]
    if sample_num > nums:
        print("采样点大于点云点数")
    range_index = [i for i in range(nums)]
    model = Model()
    pretotal = 0
    for i in range(iter):
        idx = random.sample(range_index, sample_num)
        sample_data = points[idx, :]
        normal_data = normals[idx, :]
        p1 = sample_data[0, :]
        p2 = sample_data[1, :]
        n1 = normal_data[0, :]
        n2 = normal_data[1, :]
        w = n1 + p1 - p2
        a = np.dot(n1, n1)
        b = np.dot(n1, n2)
        c = np.dot(n2, n2)
        d = np.dot(n1, w)
        e = np.dot(n2, w)
        denominator = a * c - b * b
        if denominator < 1e-8:
            sc = 0
            if b > c:
                tc = d / b
            else:
                tc = e / c
        else:
            sc = (b * e - c * d) / denominator
            tc = (a * e - b * d) / denominator
        line_pt = p1 + n1 + sc * n1
        line_dir = p2 + tc * n2 - line_pt
        line_dir = line_dir / np.linalg.norm(line_dir)
        vec = p1 - line_pt
        r = np.linalg.norm(np.cross(vec, line_dir))
        if r < min_r or r > max_r:
            continue
        dist = np.dot(line_pt, line_dir)
        t = points @ line_dir + dist
        tmpt = t.reshape(nums, 1)
        tmp_line_dir = line_dir.reshape(1, 3)
        proj_point = points - tmpt @ tmp_line_dir
        ct = np.dot(line_pt, line_dir) + dist
        center_point = line_pt - ct * line_dir
        proj_pcd = o3d.geometry.PointCloud(pcd)
        proj_pcd.points = o3d.utility.Vector3dVector(proj_point)
        pcd_tree = o3d.geometry.KDTreeFlann(proj_pcd)
        [k1, gIndices, _] = pcd_tree.search_radius_vector_3d(center_point, r + sigma)
        if r - sigma > 0:
            [k2, lIndices, _] = pcd_tree.search_radius_vector_3d(center_point, r - sigma)
        else:
            lIndices = []
        total = len(gIndices) - len(lIndices)
        if total > pretotal:
            pretotal = total
            model.point = line_pt
            model.direction = line_dir
            model.r = r
            model.lIndices = lIndices
            model.gIndices = gIndices

    print(f"圆柱中心点: {model.point}\n圆柱朝向: {model.direction}\n圆柱半径: {model.r}\n内部点数: {len(model.gIndices) - len(model.lIndices)}")
    center_location = np.array([model.point[0], model.point[1], model.point[2]])
    return center_location, model.direction, model.r

def load_point_cloud(filename):
    """
    加载点云文件，返回点的numpy数组
    """
    pcd = o3d.io.read_point_cloud(filename)
    return np.asarray(pcd.points), pcd

def fit_plane(points):
    """
    用最小二乘法拟合平面，返回平面中心和法向量
    """
    centroid = np.mean(points, axis=0)
    uu, dd, vv = np.linalg.svd(points - centroid)
    normal = vv[2]
    return centroid, normal

def visualize_plane_with_axis(pcd, centroid, normal, axis_length=0.2):
    """
    可视化点云、拟合平面法向量（轴线）
    """
    # 创建法向量箭头
    axis = o3d.geometry.LineSet()
    points = [centroid, centroid + normal * axis_length]
    axis.points = o3d.utility.Vector3dVector(points)
    axis.lines = o3d.utility.Vector2iVector([[0, 1]])
    axis.colors = o3d.utility.Vector3dVector([[1, 0, 0]])  # 红色

    o3d.visualization.draw_geometries([pcd, axis])

if __name__ == "__main__":
    # 示例：拟合点云的平面并显示法向量
    filename = "data/point_clouds/point_cloud_000.ply"
    points, pcd = load_point_cloud(filename)
    centroid, normal = fit_plane(points)
    print("平面中心:", centroid)
    print("法向量(轴线):", normal)
    visualize_plane_with_axis(pcd, centroid, normal)

    # 圆柱拟合示例
    sigma = 0.01
    min_r = 0.03
    max_r = 0.06
    sample_num = 3
    iter = 1000
    center, axis, radius = RANSAC_FIT_Cylinder(pcd, sigma, min_r, max_r, sample_num, iter)