"""
AI 服务层
- 衣物识别：调用多模态 LLM 识别衣物属性
- 搭配推荐：调用 LLM 生成搭配方案
"""

import base64
import json
import logging
from pathlib import Path

from openai import AsyncOpenAI

import config

logger = logging.getLogger(__name__)

# ============ 客户端初始化 ============

def _get_vision_client() -> AsyncOpenAI:
    """获取多模态模型客户端"""
    return AsyncOpenAI(
        base_url=config.VISION_MODEL_BASE_URL,
        api_key=config.VISION_MODEL_API_KEY,
    )


def _get_llm_client() -> AsyncOpenAI:
    """获取文本 LLM 客户端"""
    return AsyncOpenAI(
        base_url=config.LLM_BASE_URL,
        api_key=config.LLM_API_KEY,
    )


# ============ Prompt 模板 ============

CLOTHING_RECOGNITION_PROMPT = """你是一位专业的服装分析师。请仔细分析这张衣物图片，识别衣物的各项属性。

请严格按以下 JSON 格式返回，不要返回任何其他文字：

{
    "category": "上衣/裤装/裙装/外套/鞋/包/配饰",
    "sub_category": "具体类型，如T恤/衬衫/卫衣/牛仔裤/阔腿裤/连衣裙/运动鞋等",
    "color": "主色调，如白色/黑色/深蓝/浅粉等",
    "style": "风格标签，如休闲/正式/运动/甜美/学院/新中式/简约/街头等",
    "season": "适合季节，如春夏/秋冬/四季",
    "description": "一句话描述这件衣物的特点，20字以内"
}

注意：
1. category 只能是：上衣、裤装、裙装、外套、鞋、包、配饰 这7个类别之一
2. 颜色要具体，不要写"多色"，写最主要的颜色
3. description 要简洁有特色"""

OUTFIT_RECOMMEND_PROMPT = """你是小红书上最受欢迎的穿搭博主，精通各种时尚搭配风格，说话活泼有趣。

## 用户衣橱中的衣物：
{wardrobe_list}

## 任务
请从以上衣物中搭配出 3 套穿搭方案。

## 搭配原则
1. 每套必须包含上装 + 下装（或连衣裙），有合适的外套/鞋/配饰也可加入
2. 颜色要协调（同色系、对比色、或万能黑白灰搭配）
3. 风格要统一，不要把运动和正式混搭
4. 尽量让每件衣物都有机会被搭配到
5. 参考小红书当下流行的穿搭趋势

## 输出格式（严格 JSON，不要返回其他文字）
{{
    "outfits": [
        {{
            "item_ids": [衣物ID列表，如 [1, 3, 5]],
            "style_tags": ["标签1", "标签2"],
            "description": "搭配说明，用小红书博主语气，活泼有趣，50字以内",
            "reason": "为什么这样搭好看，20字以内"
        }},
        {{
            "item_ids": [衣物ID列表],
            "style_tags": ["标签1", "标签2"],
            "description": "搭配说明",
            "reason": "搭配理由"
        }},
        {{
            "item_ids": [衣物ID列表],
            "style_tags": ["标签1", "标签2"],
            "description": "搭配说明",
            "reason": "搭配理由"
        }}
    ]
}}"""


# ============ 衣物识别 ============

async def recognize_clothing(image_path: str) -> dict:
    """
    调用多模态 LLM 识别衣物属性

    Args:
        image_path: 衣物图片的本地路径

    Returns:
        识别结果字典 {category, sub_category, color, style, season, description}
    """
    client = _get_vision_client()

    # 读取图片并转 base64
    image_data = Path(image_path).read_bytes()
    base64_image = base64.b64encode(image_data).decode("utf-8")

    # 判断图片格式
    suffix = Path(image_path).suffix.lower()
    mime_map = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".webp": "image/webp"}
    mime_type = mime_map.get(suffix, "image/jpeg")

    try:
        response = await client.chat.completions.create(
            model=config.VISION_MODEL_NAME,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": CLOTHING_RECOGNITION_PROMPT},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            },
                        },
                    ],
                }
            ],
            temperature=0.1,  # 低温度，让识别结果更稳定
            max_tokens=500,
        )

        content = response.choices[0].message.content.strip()

        # 提取 JSON（兼容模型返回 markdown 代码块的情况）
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)

        # 校验必填字段
        required_fields = ["category", "color", "style"]
        for field in required_fields:
            if field not in result or not result[field]:
                raise ValueError(f"缺少必填字段: {field}")

        # 规范化 category
        valid_categories = {"上衣", "裤装", "裙装", "外套", "鞋", "包", "配饰"}
        if result["category"] not in valid_categories:
            # 尝试模糊匹配
            for cat in valid_categories:
                if cat in result["category"]:
                    result["category"] = cat
                    break
            else:
                result["category"] = "上衣"  # 兜底

        return result

    except json.JSONDecodeError as e:
        logger.error(f"AI 返回内容解析失败: {content}, error: {e}")
        # 返回默认值，让用户可以手动修正
        return {
            "category": "上衣",
            "sub_category": "未识别",
            "color": "未识别",
            "style": "未识别",
            "season": "四季",
            "description": "AI 识别失败，请手动修改",
        }
    except Exception as e:
        logger.error(f"衣物识别异常: {e}")
        raise


# ============ 搭配推荐 ============

async def recommend_outfits(wardrobe_items: list[dict]) -> list[dict]:
    """
    调用 LLM 生成搭配推荐

    Args:
        wardrobe_items: 衣物列表，每个元素是 {id, category, sub_category, color, style, description}

    Returns:
        搭配方案列表
    """
    client = _get_llm_client()

    # 构建衣橱描述
    wardrobe_lines = []
    for item in wardrobe_items:
        line = (
            f"- ID:{item['id']} | {item['category']}"
            f"({item.get('sub_category', '')}) | "
            f"颜色:{item['color']} | 风格:{item['style']}"
        )
        if item.get("ai_description"):
            line += f" | {item['ai_description']}"
        wardrobe_lines.append(line)

    wardrobe_text = "\n".join(wardrobe_lines)
    prompt = OUTFIT_RECOMMEND_PROMPT.format(wardrobe_list=wardrobe_text)

    try:
        response = await client.chat.completions.create(
            model=config.LLM_MODEL_NAME,
            messages=[
                {"role": "system", "content": "你是一位专业的穿搭顾问，只输出 JSON 格式的搭配方案。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.8,  # 稍高温度，让搭配有创意
            max_tokens=2000,
        )

        content = response.choices[0].message.content.strip()

        # 提取 JSON
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            content = content.split("```")[1].split("```")[0].strip()

        result = json.loads(content)
        outfits = result.get("outfits", [])

        # 校验每套搭配的 item_ids 都存在于衣橱中
        valid_ids = {item["id"] for item in wardrobe_items}
        validated_outfits = []
        for outfit in outfits:
            outfit_item_ids = [iid for iid in outfit.get("item_ids", []) if iid in valid_ids]
            if len(outfit_item_ids) >= 2:  # 至少 2 件衣物才算有效搭配
                outfit["item_ids"] = outfit_item_ids
                validated_outfits.append(outfit)

        if not validated_outfits:
            logger.warning("AI 没有生成有效搭配，返回兜底方案")
            return _fallback_outfits(wardrobe_items)

        return validated_outfits[:3]  # 最多返回 3 套

    except json.JSONDecodeError as e:
        logger.error(f"搭配推荐 JSON 解析失败: {content}, error: {e}")
        return _fallback_outfits(wardrobe_items)
    except Exception as e:
        logger.error(f"搭配推荐异常: {e}")
        raise


def _fallback_outfits(wardrobe_items: list[dict]) -> list[dict]:
    """
    兜底搭配方案：简单按品类配对
    当 AI 调用失败时使用
    """
    tops = [i for i in wardrobe_items if i["category"] in ("上衣", "外套")]
    bottoms = [i for i in wardrobe_items if i["category"] in ("裤装", "裙装")]

    outfits = []
    for i, top in enumerate(tops[:3]):
        if i < len(bottoms):
            bottom = bottoms[i]
            outfits.append({
                "item_ids": [top["id"], bottom["id"]],
                "style_tags": ["日常", "简约"],
                "description": f"{top['color']}{top.get('sub_category', top['category'])}搭配{bottom['color']}{bottom.get('sub_category', bottom['category'])}，简单好看！",
                "reason": "基础款百搭组合",
            })

    return outfits if outfits else [{
        "item_ids": [wardrobe_items[0]["id"]],
        "style_tags": ["单品"],
        "description": "衣橱里的衣物类型还不够丰富，再添加一些吧～",
        "reason": "需要更多衣物",
    }]
