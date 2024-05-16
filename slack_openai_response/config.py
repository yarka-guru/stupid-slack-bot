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
                           "IT-орієнтований коментар,"
                           "використовуючи програмістські жарти, прокоментуй, що ти бачиш"
    },
    "image_generation": {
        "initial_comment": "Ось згенероване DALL-E 3 зображення:",
        "model": "dall-e-3",
        "size": "1024x1024"
    },
    "diffusion_image_generation": {
        "initial_comment": "Ось згенероване Stable Diffusion зображення:",
        "model": "sd3",
        "size": "1024x1024",
        "cfg_scale": 7,
        "clip_guidance_preset": "FAST_BLUE",
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 50
    },
    "image_upscale": {
        "initial_comment": "Ось поліпшене зображення:",
        "model": "sd-upscale",
        "size": "1024x1024",
        "cfg_scale": 7,
        "clip_guidance_preset": "FAST_BLUE",
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 50
    },
    "image_edit": {
        "initial_comment": "Ось відредаговане зображення:",
        "model": "sd-edit",
        "size": "1024x1024",
        "cfg_scale": 7,
        "clip_guidance_preset": "FAST_BLUE",
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 50
    },
    "image_to_video": {
        "initial_comment": "Ось відео, створене з зображення:",
        "model": "sd-image-to-video",
        "size": "1024x1024",
        "cfg_scale": 7,
        "clip_guidance_preset": "FAST_BLUE",
        "height": 512,
        "width": 512,
        "samples": 1,
        "steps": 50
    },
    "base_prompt": (
        "Уявіть, що ви AI-консультант з IT, тебе звати BugFixer3000, який володіє дотепним гумором. "
        "Наче ти бородатий сисадмін, зроби коротенький, смішний, трошки душнуватий, IT-орієнтований коментар, "
        "використовуючи програмістські жарти, про: "
    )
}
