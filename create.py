#
import typing
from typing_extensions import NotRequired

import imgkit
import yatl


class Context(typing.TypedDict):
    icon: str
    title: str
    img: str

    template: NotRequired[str]


OG_WIDTH = 1200
OG_HEIGHT = 630


def generate_image(
    ctx: Context
):
    options = {
        'format': 'png',
        # opengraph image size is 1200x630:
        'width': OG_WIDTH,
        "height": OG_HEIGHT,
        'crop-w': OG_WIDTH,
        'crop-h': OG_HEIGHT,
        'encoding': "UTF-8",
    }

    with open(ctx.get("template", "template.html")) as f:
        rendered = yatl.render(stream=f,
                               context=ctx,
                               delimiters="[[ ]]")

    return imgkit.from_string(rendered, False, options=options)


def demo():
    img = generate_image(
        dict(
            img="https://news.su6.nl/static/icons/nu.svg",
            title="Door deze ontdekking gaat je telefoon straks tot twee keer zo lang mee",
            icon="https://media.nu.nl/m/zh2x98aada6s_sqr256.jpg/door-deze-ontdekking-gaat-je-telefoon-straks-tot-twee-keer-zo-lang-mee.jpg",
        )
    )

    with open("temp.png", "wb") as f:
        f.write(img)


if __name__ == '__main__':
    demo()
