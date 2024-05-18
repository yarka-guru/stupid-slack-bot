config = {
    "text_commands": {
        "generate_image": "згенеруй зображення:",
        "generate_diffusion_image": "generate image:"
    },
    "image_analysis": {
        "model": "gpt-4o",
        "max_tokens": 300,
        "analysis_prompt": (
            "Уявіть, що ви AI-консультант з IT, тебе звати BugFixer3000, який володіє дотепним гумором. "
            "Наче ти бородатий сисадмін, зроби коротенький, смішний, трошки душнуватий, "
            "IT-орієнтований коментар, використовуючи програмістські жарти, прокоментуй, що ти бачиш"
        )
    },
    "image_generation": {
        "initial_comment": "Ось згенероване DALL-E 3 зображення:",
        "model": "dall-e-3",
        "size": "1024x1024"
    },
    "diffusion_image_generation": {
        "initial_comment": "Ось згенероване Stable Diffusion зображення:",
        "endpoint": "https://api.stability.ai/v2beta/stable-image/generate/sd3",
        "model": "sd3-turbo",
        "cfg_scale": 7,
        "clip_guidance_preset": "FAST_BLUE",
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 150,
        "output_format": "jpeg"
    },
    "base_prompt": (
        "Уявіть, що ви AI-консультант з IT, тебе звати BugFixer3000, ти володієш дотепним гумором. "
        "Наче ти бородатий сисадмін, зроби коротенький, ше раз повторюю коротенький! ну дуже смішний, "
        "трошки душнуватий, IT-орієнтований коментар, використовуючи програмістські жарти, про: "
    ),
    "stop_word": "завали!"
}
