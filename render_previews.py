"""Export GIF previews and PNG frames from a v2 pet atlas using Pillow."""

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROW_DURATIONS = {
    'idle': [280, 110, 110, 140, 140, 320],
    'running-right': [120] * 7 + [220],
    'running-left': [120] * 7 + [220],
    'waving': [140, 140, 140, 280],
    'jumping': [140, 140, 140, 140, 280],
    'failed': [140] * 7 + [240],
    'waiting': [150] * 5 + [260],
    'running': [120] * 5 + [220],
    'review': [150] * 5 + [280],
}


def save_gif(frames, durations, destination):
    frames[0].save(
        destination, save_all=True, append_images=frames[1:],
        duration=durations, loop=0, disposal=2, optimize=False,
    )


def render(atlas_path, output):
    atlas = Image.open(atlas_path).convert('RGBA')
    if atlas.size != (1536, 2288):
        raise ValueError(f'Expected a 1536x2288 v2 atlas, got {atlas.size}')
    output.mkdir(parents=True, exist_ok=True)
    font = ImageFont.load_default(size=18)

    def cell(row, column):
        return atlas.crop((column * 192, row * 208, (column + 1) * 192, (row + 1) * 208))

    state_frames = {}
    all_frames = []
    all_durations = []
    for row, (state, durations) in enumerate(ROW_DURATIONS.items()):
        frames = [cell(row, column) for column in range(len(durations))]
        state_frames[state] = frames
        folder = output / 'frames' / state
        folder.mkdir(parents=True, exist_ok=True)
        for index, frame in enumerate(frames):
            frame.save(folder / f'{index:02d}.png')
            canvas = Image.new('RGBA', (384, 460), '#f4f6fc')
            canvas.alpha_composite(frame.resize((384, 416), Image.Resampling.NEAREST), (0, 36))
            ImageDraw.Draw(canvas).text((12, 9), f'{state} | {index + 1}', font=font, fill='#152747')
            all_frames.append(canvas)
            all_durations.append(durations[index])
        save_gif(frames, durations, output / f'{state}.gif')
    save_gif(all_frames, all_durations, output / 'all-states.gif')

    jump_frames = state_frames['idle'] + state_frames['jumping'] + state_frames['idle']
    jump_durations = ROW_DURATIONS['idle'] + ROW_DURATIONS['jumping'] + ROW_DURATIONS['idle']
    save_gif(jump_frames, jump_durations, output / 'idle-jump-idle.gif')
    look_frames = [cell(9 + index // 8, index % 8) for index in range(16)]
    save_gif(look_frames, [180] * 16, output / 'look-loop.gif')

    selected = [(0, 0, 'Idle'), (3, 1, 'Wave'), (4, 2, 'Jump peak'), (7, 3, 'Thinking')]
    stills = Image.new('RGBA', (768, 238), '#f4f6fc')
    draw = ImageDraw.Draw(stills)
    for index, (row, column, label) in enumerate(selected):
        draw.text((index * 192 + 8, 8), label, font=font, fill='#152747')
        stills.alpha_composite(cell(row, column), (index * 192, 30))
    stills.convert('RGB').save(output / 'four-stills.png')
    print(f'Previews saved to {output.resolve()}')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--atlas', type=Path, default=Path(__file__).with_name('spritesheet.png'))
    parser.add_argument('--output-dir', type=Path, default=Path('previews'))
    arguments = parser.parse_args()
    render(arguments.atlas, arguments.output_dir)
