from flask import Flask, request, jsonify
from dashscope import MultiModalConversation, Generation
import dashscope
import os
import re

# 从环境变量读取 API Key
dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

def is_multiple_choice(question: str) -> bool:
    patterns = [r'\b[A-D]\.\s', r'\([A-D]\)', r'选项[：:]?\s*[A-D]', r'四个选项']
    return any(re.search(p, question, re.IGNORECASE) for p in patterns)

def handler(request):
    if request.method != 'POST':
        return jsonify({"error": "Only POST allowed"}), 405

    data = request.get_json()
    question = data.get('question', '').strip()
    user_answer = data.get('user_answer', '').strip()
    image_base64 = data.get('image', '')

    if not question or not user_answer:
        return jsonify({"error": "题目和答案不能为空"}), 400

    is_mc = is_multiple_choice(question)
    system_prompt = (
        "你是一位严谨的学科教师，请对以下题目进行批改。\n"
        "请严格按以下格式输出：\n"
        "【判断】正确/错误\n"
        f"【{'正确答案' if is_mc else '参考答案'}】...\n"
        "【解析】...\n"
        "【考点】...\n"
        "【错因】..."
    )
    user_prompt = f"题目：{question}\n我的答案：{user_answer}"

    try:
        if image_base64:
            messages = [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': [{'image': image_base64}, {'text': user_prompt}]}
            ]
            response = MultiModalConversation.call(model='qwen-vl-plus', messages=messages)
        else:
            response = Generation.call(
                model='qwen-plus',
                messages=[{'role': 'system', 'content': system_prompt}, {'role': 'user', 'content': user_prompt}]
            )

        if response.status_code == 200:
            ai_text = response.output.choices[0].message.content
            return jsonify({"ai_feedback": ai_text})
        else:
            return jsonify({"error": f"AI 错误: {response.code}"}), 500
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Vercel 入口
def grade(req):
    from vercel_wsgi import serve
    app = Flask(__name__)
    CORS(app)  # 注意：Vercel 中需处理 CORS
    @app.route('/api/grade', methods=['POST'])
    def route():
        return handler(req)
    return serve(app, req)
