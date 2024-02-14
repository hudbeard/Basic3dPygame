import time
import pygame
from pygame3dengine import Pygame3dEngine

engine = Pygame3dEngine()
pygame.mouse.set_visible(False)
model = engine.load_model("cube.csv")
scene = [model]

while engine.running:
    engine.check_for_quit()
    keys = pygame.key.get_pressed()
    if keys[pygame.K_q]:
        pygame.quit()

    if keys[pygame.K_w]:
        engine.camera.position[-1] += 0.1
    if keys[pygame.K_s]:
        engine.camera.position[-1] += -0.1
    if keys[pygame.K_a]:
        engine.camera.position[0] += -0.1
    if keys[pygame.K_d]:
        engine.camera.position[0] += 0.1
    if keys[pygame.K_SPACE]:
        engine.camera.position[1] += 0.1
    if keys[pygame.K_LSHIFT]:
        engine.camera.position[1] -= 0.1

    x, y = engine.to_rotation_coordinates(*pygame.mouse.get_pos())
    pygame.mouse.set_pos(engine.center)
    engine.camera.rotation[0] += y / 2
    engine.camera.rotation[1] += -x / 2
    pygame.draw.circle(engine.screen, "white", engine.center, 3)

    start = time.time()
    projected_mesh = engine.project_scene(scene)
    end = time.time()
    project_latency = end - start

    start = time.time()
    engine.render_scene(projected_mesh)
    end = time.time()
    render_latency = end - start

    text_surface = engine.font.render(f"Rotation: {engine.camera.rotation} | Position: {engine.camera.position} | {project_latency} | {render_latency}", True, (255, 255, 255))
    engine.screen.blit(text_surface, (0, 0))
    engine.flip()
