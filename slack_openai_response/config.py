config = {
    "text_commands": {
        "generate_image": "згенеруй зображення:",
        "generate_diffusion_image": "створи зображення:",
        "upscale_image": "поліпши зображення:",
        "edit_image": "відредагуй зображення:",
        "image_to_video": "створи відео:"
    },
    "image_analysis": {
        "model": "gpt-4o",
        "max_tokens": 300,
        "analysis_prompt": "Уявіть, що ви AI-консультант з IT, тебе звати BugFixer3000, який володіє дотепним гумором. "
                           "Наче ти бородатий сисадмін, зроби коротенький, смішний, трошки душнуватий, "
                           "IT-орієнтований коментар, використовуючи програмістські жарти, прокоментуй, що ти бачиш"
    },
    "image_generation": {
        "initial_comment": "Ось згенероване DALL-E 3 зображення:",
        "model": "dall-e-3",
        "size": "1024x1024"
    },
    "diffusion_image_generation": {
        "initial_comment": "Ось згенероване Stable Diffusion зображення:",
        "endpoint": "https://api.stability.ai/v2beta/stable-image/generate/sd3",
        "model": "sd3",
        "cfg_scale": 7,
        "clip_guidance_preset": "FAST_BLUE",
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 50,
        "output_format": "jpeg"
    },
    "image_upscale": {
        "initial_comment": "Ось поліпшене зображення:",
        "endpoint": "https://api.stability.ai/v2beta/stable-image/upscale/creative",
        "prompt": "Provide your prompt here",
        "output_format": "webp"
    },
    "image_edit": {
        "initial_comment": "Ось відредаговане зображення:",
        "endpoint": "https://api.stability.ai/v2beta/stable-image/edit/inpaint",
        "prompt": "Provide your prompt here",
        "mask": "path/to/your/mask.png",
        "output_format": "webp"
    },
    "image_to_video": {
        "initial_comment": "Ось відео, створене з зображення:",
        "endpoint": "https://api.stability.ai/v2beta/image-to-video",
        "seed": 0,
        "cfg_scale": 1.8,
        "motion_bucket_id": 127
    },
    "base_prompt": (
        "Уявіть, що ви AI-консультант з IT, тебе звати BugFixer3000, який володіє дотепним гумором. "
        "Наче ти бородатий сисадмін, зроби коротенький, смішний, трошки душнуватий, IT-орієнтований коментар, "
        "використовуючи програмістські жарти, про: "
    )
}
