import math
from dataclasses import dataclass
import numpy
import pygame
import csv


class Pygame3dEngine:
    def __init__(self):
        pygame.init()
        self.display = pygame.display.Info().current_w, pygame.display.Info().current_h
        self.focal_length = 85
        self.running = True
        self.scale = 5
        self.center = self.to_screen_coordinates(0, 0)
        self.camera = Camera(numpy.array([0., 0., 0.]), numpy.array([0., 90., 0.]))
        self.camera_clipping_planes = [
            ClippingPlane((0, 0, 1), self.focal_length),
            ClippingPlane((1 / math.sqrt(2), 0, 1 / math.sqrt(2)), 0),
            ClippingPlane((-1 / math.sqrt(2), 0, 1 / math.sqrt(2)), 0),
            ClippingPlane((0, 1 / math.sqrt(2), 1 / math.sqrt(2)), 0),
            ClippingPlane((0, -1 / math.sqrt(2), 1 / math.sqrt(2)), 0),
        ]
        self.font = pygame.font.SysFont('Comic Sans', 12)
        self.screen = pygame.display.set_mode(self.display, pygame.FULLSCREEN)
        self.clock = pygame.time.Clock()

    @staticmethod
    def load_model(filename: str) -> dataclass:
        with open(filename) as csv_file:
            reader = list(csv.DictReader(csv_file))
            triangle = [Triangle(*[int(i) for i in list(row.values())[:3]], row["color"]) for row in reader if
                        row["color"]]
            vertices = numpy.array([[float(i) for i in list(row.values())[:3]] for row in reader if not row["color"]])
        return Model(vertices, triangle, [-2, 0, 0], numpy.array([0, 0, 0]))

    def check_for_quit(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

    def to_screen_coordinates(self, x: float, y: float) -> tuple[float, float]:
        return x + self.display[0] / 2, y + self.display[1] / 2

    def to_rotation_coordinates(self, x: float, y: float) -> tuple[float, float]:
        return x - self.display[0] / 2, y - self.display[1] / 2

    def project_mesh(self, model: dataclass):
        vertices = self.rotate(model.vertices, rotation=model.rotation)
        vertices = self.translate(vertices, translation=model.position)
        vertices = self.translate(vertices, translation=self.camera.position)
        vertices = self.rotate(vertices, rotation=self.camera.rotation)
        triangles = [t for t in model.triangles if all([self.clip_triangle(p, t, vertices) for p in self.camera_clipping_planes])]
        projected_x = [(vertex[0] * self.focal_length) / vertex[-1] for vertex in vertices]
        projected_y = [(vertex[1] * self.focal_length) / vertex[-1] for vertex in vertices]
        return ((self.to_screen_coordinates(projected_x[triangle.a] * self.scale, projected_y[triangle.a] * self.scale),
                 self.to_screen_coordinates(projected_x[triangle.b] * self.scale, projected_y[triangle.b] * self.scale),
                 self.to_screen_coordinates(projected_x[triangle.c] * self.scale, projected_y[triangle.c] * self.scale),
                 triangle.color) for triangle in triangles)

    def project_scene(self, scene):
        return [self.project_mesh(mesh) for mesh in scene]

    def render_mesh(self, projected_mesh):
        for triangle in projected_mesh:
            pygame.draw.polygon(self.screen, triangle[-1], triangle[:3], 5)

    def render_scene(self, projected_scene):
        for projected_mesh in projected_scene:
            self.render_mesh(projected_mesh)

    @staticmethod
    def translate(vertices, translation):
        return vertices + translation

    @staticmethod
    def rotate(vertices, rotation):
        rotation = rotation * math.pi / 180
        rotation_z_matrix = numpy.array([
            [math.cos(rotation[2]), -math.sin(rotation[2]), 0],
            [math.sin(rotation[2]), math.cos(rotation[2]), 0],
            [0, 0, 1],
        ])
        rotation_y_matrix = numpy.array([
            [math.cos(rotation[1]), 0, math.sin(rotation[1])],
            [0, 1, 0],
            [-math.sin(rotation[1]), 0, math.cos(rotation[1])],
        ])
        rotation_x_matrix = numpy.array([
            [1, 0, 0],
            [0, math.cos(rotation[0]), -math.sin(rotation[0])],
            [0, math.sin(rotation[0]), math.cos(rotation[0])],
        ])
        x_rotated = numpy.tensordot(rotation_x_matrix, vertices, axes=(1, 1)).T
        xy_rotated = numpy.tensordot(rotation_y_matrix, x_rotated, axes=(1, 1)).T
        xyz_rotated = numpy.tensordot(rotation_z_matrix, xy_rotated, axes=(1, 1)).T
        return xyz_rotated

    def clip_triangle(self, plane, triangle, vertices):
        distances = numpy.array([
            self.get_signed_distance(plane, vertices[triangle.a]),
            self.get_signed_distance(plane, vertices[triangle.b]),
            self.get_signed_distance(plane, vertices[triangle.c])
        ])

        if all(distances > 0):
            return True
        elif all(distances < 0):
            return False
        else:
            return True

    @staticmethod
    def get_signed_distance(plane, vertex):
        normal_x, normal_y, normal_z = plane.normal
        vertex_x, vertex_y, vertex_z = vertex
        return vertex_x * normal_x + (vertex_y * normal_y) + (vertex_z * normal_z) + plane.distance_to_origin

    def flip(self):
        pygame.display.flip()
        self.screen.fill("black")
        self.clock.tick(60)


@dataclass
class Triangle:
    a: int
    b: int
    c: int
    color: str


@dataclass
class Camera:
    position: numpy.ndarray
    rotation: numpy.ndarray


@dataclass
class Model:
    vertices: numpy.ndarray
    triangles: list
    position: list
    rotation: numpy.ndarray


@dataclass
class ClippingPlane:
    normal: tuple
    distance_to_origin: float
