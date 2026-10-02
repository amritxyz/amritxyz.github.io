+++
title = 'Building My Own 2D Graphics Library in C'
date = 2026-08-07
+++

*In this blog, I will call the library "libgfx".*

I am a university student and currently learning OpenGL. When I started, I was surprised. To draw a simple shape on the screen, you need a lot of setup. First, you create a window. Then you load the OpenGL functions, compile shaders, and create buffers. Only after that you can draw something. I thought drawing a triangle would be very easy, but it was not.

So I built libgfx. It is a small 2D graphics library written in C99, and it works on Linux, macOS, and Windows. The idea is simple: open a window and draw things with only a few lines of code. I also wanted to see what OpenGL is doing, not hide it. I thought the best way to understand all the setup was to write it myself.

I kept the libgfx small on purpose. It can:

- create a window with an OpenGL 3.3 Core context
- limit the frame rate to 60 FPS using vsync
- draw pixels, lines, and regular polygons with `draw_pixel`, `draw_line`, and `draw_poly`
- read keyboard input using callbacks or functions like `gfx_is_key_down` and `gfx_is_key_pressed`

It uses only two libraries. GLFW gives the window and the input. GLAD loads the modern OpenGL functions. I did not use OpenGL's old fixed-function pipeline. I used shaders (GLSL 3.30) from the start because I want to learn the modern OpenGL pipeline.

The most important thing I learned was about coordinates. OpenGL uses values from -1 to 1. But I wanted to work in pixel coordinates with `(0, 0)` at the top-left corner, like a most 2D graphics libraries. The solution is an orthographic projection matrix. It transforms pixel coordinates into the values OpenGL expects:

```c
float left = 0.0f, right = (float)width;
float bottom = (float)height, top = 0.0f;

float ortho[16] = {0};
ortho[0]  = 2.0f / (right - left);
ortho[5]  = 2.0f / (top - bottom);
ortho[12] = -(right + left) / (right - left);
ortho[13] = -(top + bottom) / (top - bottom);
```

To be honest, I did not understand this when I first read about it. It became clear only when I saw my shapes appear in the right place.

I learned a lot from my mistakes:

- **Wrong colors.** I was using color values from 0 to 255, but `glClearColor` expects values from 0.0 to 1.0. Because of this, orange looked yellow. I fixed it with a macro that converts the values automatically.
- **Thick borders.** `glLineWidth` with a value above 1.0 does not work reliably in core profile on macOS and Windows. So I implemented thick borders myself. For each edge, I find a perpendicular direction and draw a rectangle using two triangles.
- **VAO and VBO mix-up.** In `draw_pixel`, I used `ctx->vao` instead of `ctx->vbo` in `glBindBuffer`. Both are just integer handlers, so this mistake is easy to make and hard to find.

The library is not finished. Right now, every shape sends its vertices to the GPU and requires separate draw call. This is simple, but it is slow. My next big step is to implement a batch renderer, which can draw many shapes together. Also, `draw_poly` uses fixed-size arrays with a limit of 1,000 sides. There is no mouse input and no window resizing yet.

I'm not saying that everyone should make their own graphics library. Raylib and SDL are already very good, and I would use them for a real project. But building something small helped me understand what these tools do for us.

If you want to try it, clone it from Codeberg: `https://codeberg.org/nyxvoid/libgfx.git`. I am still learning, so if you find a mistake in my OpenGL code, please tell me.
