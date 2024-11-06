from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from xue import HTML, Head, Body, Div, xue_initialize, Script
from xue.components import input, button, card
import anthropic
import asyncio
import base64
from io import BytesIO

app = FastAPI()
xue_initialize(tailwind=True)

# 初始化 Claude API 客户端
claude = anthropic.AsyncAnthropic(api_key="your-api-key")

@app.get("/", response_class=HTMLResponse)
async def root():
    result = HTML(
        Head(
            # 添加下载SVG的脚本
            Script("""
                function downloadSVG() {
                    const svg = document.querySelector('#logo-display svg');
                    if (!svg) return;

                    const svgData = new XMLSerializer().serializeToString(svg);
                    const blob = new Blob([svgData], {type: 'image/svg+xml'});
                    const url = URL.createObjectURL(blob);

                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'logo.svg';
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                }
            """, id="downloadsvg-script"),
            title="LogoSpark - AI Logo Generator",
        ),
        Body(
            Div(
                card.Card(
                    card.CardHeader(
                        card.CardTitle("LogoSpark"),
                        card.CardDescription("Generate beautiful logos using AI")
                    ),
                    card.CardContent(
                        Div(
                            input.input(
                                type="text",
                                id="logo-prompt",
                                placeholder="Describe your logo idea...",
                                class_="w-full mb-4"
                            ),
                            Div(
                                button.button(
                                    "Generate Logo",
                                    variant="primary",
                                    class_="mr-2",
                                    hx_post="/generate",
                                    hx_target="#logo-display",
                                    hx_include="#logo-prompt"
                                ),
                                button.button(
                                    "Regenerate",
                                    variant="secondary",
                                    class_="mr-2",
                                    hx_post="/generate",
                                    hx_target="#logo-display",
                                    hx_include="#logo-prompt",
                                    style="display: none;",
                                    id="regenerate-btn"
                                ),
                                button.button(
                                    "Download SVG",
                                    variant="secondary",
                                    onclick="downloadSVG()",
                                    style="display: none;",
                                    id="download-btn"
                                ),
                                class_="flex justify-start"
                            ),
                            class_="mb-4"
                        ),
                        Div(
                            id="logo-display",
                            class_="w-full h-64 flex items-center justify-center border-2 border-dashed border-gray-300 dark:border-gray-600 rounded-lg"
                        ),
                    ),
                ),
                class_="container mx-auto max-w-2xl p-4"
            )
        )
    ).render()
    return result

@app.post("/generate", response_class=HTMLResponse)
async def generate_logo(request: Request):
    form_data = await request.form()
    prompt = form_data.get("logo-prompt")

    # 构建给 Claude 的提示
    system_prompt = """You are a logo designer. Create an SVG logo based on the user's description.
    The SVG should be simple, modern, and professional.
    Return only the SVG code without any explanation or markdown."""

    user_prompt = f"Create a logo that looks like this: {prompt}. Return only the SVG code."

    try:
        # 调用 Claude API
        response = await claude.messages.create(
            model="claude-3-opus-20240229",
            max_tokens=1000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": user_prompt
            }]
        )

        svg_code = response.content[0].text

        # 返回 SVG 和控制按钮
        result = Div(
            Div(svg_code, class_="w-full h-full"),
            Script("""
                document.getElementById('regenerate-btn').style.display = 'inline-block';
                document.getElementById('download-btn').style.display = 'inline-block';
            """),
            class_="w-full h-full flex items-center justify-center"
        ).render()

        return result

    except Exception as e:
        return Div(
            f"Error generating logo: {str(e)}",
            class_="text-red-500"
        ).render()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)