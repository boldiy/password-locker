from PIL import Image, ImageDraw


def create_lock_icon(sizes=(256, 128, 64, 48, 32, 16)):
    # 生成多个尺寸的锁图标并保存为 icon.ico
    images = []
    for size in sizes:
        img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        # 锁体
        body_w = int(size * 0.6)
        body_h = int(size * 0.45)
        body_x = (size - body_w) // 2
        body_y = int(size * 0.35)
        draw.rounded_rectangle([body_x, body_y, body_x + body_w, body_y + body_h], radius=size//10, fill=(40, 120, 200, 255))
        # 锁眼
        eye_r = max(2, size // 18)
        eye_x = size // 2
        eye_y = body_y + body_h // 2
        draw.ellipse([eye_x - eye_r, eye_y - eye_r, eye_x + eye_r, eye_y + eye_r], fill=(255, 255, 255, 255))
        # 锁环
        ring_w = int(size * 0.6)
        ring_h = int(size * 0.5)
        ring_x = (size - ring_w) // 2
        ring_y = int(size * 0.05)
        # 画半透明白色弧形作为锁环
        draw.arc([ring_x, ring_y, ring_x + ring_w, ring_y + ring_h], start=200, end=340, fill=(40, 120, 200, 255), width=max(2, size//14))
        images.append(img)

    images[0].save('icon.ico', format='ICO', sizes=[(s, s) for s in sizes])


if __name__ == '__main__':
    create_lock_icon()
