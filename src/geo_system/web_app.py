"""
GEO Web App - Web界面进行GEO检测
"""
import json
import os
import uuid
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory
from werkzeug.utils import secure_filename

from .intent_engine import generate_prompts, dedupe_prompts
from .model_testing_engine import run_scan
from .schema import Prompt

app = Flask(__name__, template_folder='../../web/templates', static_folder='../../web/static')
app.config['UPLOAD_FOLDER'] = '../../data/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

# 确保上传目录存在
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/scan', methods=['POST'])
def run_geo_scan():
    """执行GEO扫描"""
    data = request.get_json()
    
    # 获取项目信息
    brand = data.get('brand', '')
    domain = data.get('domain', '')
    description = data.get('description', '')
    seed_keywords = data.get('seed_keywords', '')
    models = data.get('models', 'openai:live,claude:live,gemini:live')
    
    if not brand or not domain:
        return jsonify({'error': '请提供品牌名和域名'}), 400
    
    # 解析关键词
    seeds = [s.strip() for s in seed_keywords.split(',') if s.strip()]
    if not seeds:
        seeds = [brand, domain]
    
    # 生成提示词
    prompts_raw = generate_prompts(seeds, count=50)
    prompts = dedupe_prompts(prompts_raw)
    
    # 加载适配器配置
    adapter_config = _load_adapter_config()
    brand_terms = [brand, domain]
    
    # 运行扫描
    model_list = [m.strip() for m in models.split(',') if m.strip()]
    try:
        results = run_scan(model_list, prompts, brand_terms=brand_terms, adapter_config=adapter_config)
    except Exception as e:
        return jsonify({'error': f'扫描失败: {str(e)}'}), 500
    
    # 汇总结果
    summary = _summarize_results(results, prompts)
    
    return jsonify({
        'success': True,
        'project': {'brand': brand, 'domain': domain, 'description': description},
        'prompts_generated': len(prompts),
        'summary': summary,
        'detailed_results': [r.to_dict() for r in results]
    })


@app.route('/api/upload-config', methods=['POST'])
def upload_config():
    """上传配置文件进行批量检测"""
    if 'file' not in request.files:
        return jsonify({'error': '没有文件'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': '未选择文件'}), 400
    
    # 保存文件
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{filename}")
    file.save(filepath)
    
    # 解析配置
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            config = json.load(f)
    except Exception as e:
        return jsonify({'error': f'文件解析失败: {str(e)}'}), 400
    
    # 批量扫描
    results = []
    for project in config.get('projects', []):
        brand = project.get('brand', '')
        domain = project.get('domain', '')
        keywords = project.get('keywords', '')
        
        seeds = [s.strip() for s in keywords.split(',')] if keywords else [brand, domain]
        prompts = dedupe_prompts(generate_prompts(seeds, count=30))
        
        adapter_config = _load_adapter_config()
        model_list = config.get('models', 'openai:live').split(',')
        
        scan_results = run_scan(model_list, prompts, brand_terms=[brand, domain], adapter_config=adapter_config)
        
        results.append({
            'brand': brand,
            'domain': domain,
            'summary': _summarize_results(scan_results, prompts)
        })
    
    return jsonify({'success': True, 'results': results})


def _load_adapter_config():
    """加载适配器配置"""
    config_path = Path(__file__).parent.parent.parent / 'data' / 'adapter_config.json'
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}


def _summarize_results(results, prompts):
    """汇总扫描结果"""
    total = len(results)
    mentioned = sum(1 for r in results if r.mention_level != 'none')
    cited = sum(1 for r in results if r.cited_urls)
    recommended = sum(1 for r in results if r.recommendation == 'recommended')
    
    # 按模型分组
    by_model = {}
    for r in results:
        model = r.model
        if model not in by_model:
            by_model[model] = {'mentions': 0, 'citations': 0, 'recommendations': 0}
        if r.mention_level != 'none':
            by_model[model]['mentions'] += 1
        if r.cited_urls:
            by_model[model]['citations'] += 1
        if r.recommendation == 'recommended':
            by_model[model]['recommendations'] += 1
    
    return {
        'total_scans': total,
        'mention_rate': round(mentioned / total * 100, 1) if total else 0,
        'citation_rate': round(cited / total * 100, 1) if total else 0,
        'recommendation_rate': round(recommended / total * 100, 1) if total else 0,
        'by_model': by_model
    }


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
