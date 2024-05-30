config = {
    "text_commands": {
        "generate_image": "згенеруй зображення",
        "generate_diffusion_image": "generate image"
    },
    "image_analysis": {
        "model": "gpt-4o",
        "max_tokens": 300,
        "analysis_prompt": (
            "Уявіть, що ви AI-консультант з IT, ваше ім'я BugFixer3000, який володіє дотепним гумором. "
            "Наче бородатий системний адміністратор, зробіть короткий, веселий, трохи саркастичний і IT-орієнтований коментар "
            "до наступного мему чи повідомлення. Не перевищуйте 20 слів. Пам'ятайте, гумор повинен бути актуальним до контексту."
        )
    },
    "image_generation": {
        "initial_comment": "Ось згенероване DALL-E 3 зображення:",
        "model": "dall-e-3",
        "size": "1024x1024",
        "n": 1
    },
    "diffusion_image_generation": {
        "initial_comment": "Ось згенероване Stable Diffusion зображення:",
        "endpoint": "https://api.stability.ai/v2beta/stable-image/generate/sd3",
        "model": "sd3-turbo",
        "aspect_ratio": "1:1",
        "mode": "text-to-image",
        "output_format": "jpeg",
        "cfg_scale": 7,
        "clip_guidance_preset": "FAST_BLUE",
        "height": 1024,
        "width": 1024,
        "samples": 1,
        "steps": 150
    },
    "base_prompt": (
        "Уявіть, що ви AI-консультант з IT, ваше ім'я BugFixer3000. Ви володієте дотепним гумором, наче бородатий системний адміністратор. "
        "Зробіть короткий, веселий, трохи саркастичний і IT-орієнтований коментар до наступного мему чи повідомлення. Не перевищуйте 20 слів. "
        "Пам'ятайте, гумор повинен бути актуальним до контексту."
    ),
    "stop_word": "завали!"
}