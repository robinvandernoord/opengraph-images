# Opengraph Images

![](example.png)

Requires `wkhtmltopdf` to be installed (`sudo apt install -y wkhtmltopdf` or a binary from [https://wkhtmltopdf.org/downloads.html](https://wkhtmltopdf.org/downloads.html)).

By default, the template is pretty simple as can be seen above. 
`template.html` can be modified or a different option can be passed to `generate_image`.
This template is rendered using [yatl](https://github.com/web2py/yatl).  
`wkhtmltopdf` supports most styles a browser would!

## Usage

```python
from opengraph_images import generate_image

img: bytes = generate_image({
    "title": "Hello World",
    "icon": "https://example.com/icon.png",
    "img": "https://example.com/image.png",
    # optional:
    "template": "other_template.html",
})
```
