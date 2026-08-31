#!/usr/bin/env python3
"""
AI 활용도 평가 모듈 (AI Utilization Evaluator)

GitHub 레포지토리의 AI/ML 활용 수준을 다면적으로 평가합니다.

평가 항목:
  1. AI/ML 라이브러리 사용 (의존성 분석)
  2. AI 설정 파일 존재 (Copilot, Cursor, Aider 등)
  3. AI 관련 태그/토픽
  4. AI 모델 파일 (*.pt, *.onnx, *.safetensors 등)
  5. AI 에이전트 프레임워크 사용
  6. 학습/추론 스크립트 존재
  7. 노트북/데이터셋 존재
  8. AI 문서화 수준
"""

import re
from dataclasses import dataclass, field
from typing import Optional

# ─── AI 관련 패키지 매핑 ──────────────────────────────────────────────────────

# 언어별 AI/ML 패키지 사전
AI_PACKAGES = {
    # Python
    "python": {
        # 딥러닝 프레임워크
        "tensorflow": "Deep Learning",
        "keras": "Deep Learning",
        "torch": "Deep Learning",
        "pytorch": "Deep Learning",
        "jax": "Deep Learning",
        "flax": "Deep Learning",
        "mxnet": "Deep Learning",
        "paddlepaddle": "Deep Learning",
        # 머신러닝
        "scikit-learn": "Machine Learning",
        "sklearn": "Machine Learning",
        "xgboost": "Machine Learning",
        "lightgbm": "Machine Learning",
        "catboost": "Machine Learning",
        "statsmodels": "Statistics",
        # NLP
        "transformers": "NLP/LLM",
        "huggingface-hub": "NLP/LLM",
        "tokenizers": "NLP/LLM",
        "sentence-transformers": "NLP/LLM",
        "spacy": "NLP",
        "nltk": "NLP",
        "gensim": "NLP",
        "langchain": "LLM Agent",
        "langchain-core": "LLM Agent",
        "langchain-community": "LLM Agent",
        "llamaindex": "LLM Agent",
        "llama-index": "LLM Agent",
        "openai": "LLM API",
        "anthropic": "LLM API",
        "cohere": "LLM API",
        "google-generativeai": "LLM API",
        "mistralai": "LLM API",
        # 컴퓨터 비전
        "opencv-python": "Computer Vision",
        "opencv-contrib-python": "Computer Vision",
        "pillow": "Image Processing",
        "torchvision": "Computer Vision",
        "ultralytics": "Object Detection",
        "yolov5": "Object Detection",
        "segment-anything": "Segmentation",
        # 오디오/음성
        "whisper": "Speech Recognition",
        "openai-whisper": "Speech Recognition",
        "librosa": "Audio Processing",
        "torchaudio": "Audio Processing",
        # 생성 AI
        "diffusers": "Generative AI",
        "stable-diffusion": "Generative AI",
        "accelerate": "ML Training",
        "deepspeed": "ML Training",
        "bitsandbytes": "ML Training",
        # MLOps
        "mlflow": "MLOps",
        "wandb": "MLOps",
        "dvc": "Data Versioning",
        "kubeflow": "MLOps",
        "bentoml": "MLOps",
        "ray": "Distributed ML",
        "ray[serve]": "Distributed ML",
        # 데이터 처리
        "pandas": "Data Processing",
        "numpy": "Numerical Computing",
        "scipy": "Scientific Computing",
        # 에이전트/자동화
        "autogen": "AI Agent",
        "crewai": "AI Agent",
        "metagpt": "AI Agent",
        "autogpt": "AI Agent",
        "babyagi": "AI Agent",
        "superagi": "AI Agent",
        "haystack": "AI Agent",
        "dspy": "AI Agent",
    },
    # JavaScript/TypeScript
    "javascript": {
        "@tensorflow/tfjs": "Deep Learning",
        "tensorflow.js": "Deep Learning",
        "ml5": "ML Library",
        "brain.js": "Neural Network",
        "natural": "NLP",
        "compromise": "NLP",
        "onnxruntime-node": "ML Inference",
        "onnxruntime-web": "ML Inference",
        "openai": "LLM API",
        "langchain": "LLM Agent",
        "llamaindex": "LLM Agent",
        "ai": "AI SDK",
        "genkit": "AI SDK",
        "ai/prompts": "AI SDK",
        "vectordb": "Vector DB",
        "chromadb": "Vector DB",
        "pinecone-client": "Vector DB",
        "@pinecone-database/pinecone": "Vector DB",
        "weaviate-client": "Vector DB",
        "qdrant": "Vector DB",
    },
    # Rust
    "rust": {
        "candle": "Deep Learning",
        "burn": "Deep Learning",
        "tch": "Deep Learning",
        "linfa": "Machine Learning",
        "smartcore": "Machine Learning",
        "ort": "ML Inference",
        "whisper-rs": "Speech Recognition",
    },
    # Java
    "java": {
        "deeplearning4j": "Deep Learning",
        "dl4j": "Deep Learning",
        "weka": "Machine Learning",
        "smile": "Machine Learning",
        "tribuo": "Machine Learning",
    },
    # Go
    "go": {
        "gonum": "Numerical Computing",
        "gorgonia": "Deep Learning",
        "tfgo": "Deep Learning",
        "org.golang:gonum": "Numerical Computing",
    },
}

# ─── AI 관련 파일 패턴 ──────────────────────────────────────────────────────

AI_CONFIG_FILES = {
    # GitHub Copilot
    ".github/copilot-instructions.md": "GitHub Copilot",
    "copilot-instructions.md": "GitHub Copilot",
    ".copilot": "GitHub Copilot",
    ".github/copilot.yml": "GitHub Copilot",
    # Cursor
    ".cursorrules": "Cursor AI",
    ".cursorignore": "Cursor AI",
    ".cursor/config.json": "Cursor AI",
    # Aider
    ".aider": "Aider",
    ".aider.conf.yml": "Aider",
    ".aider.conf.yaml": "Aider",
    ".aider.model.settings.yml": "Aider",
    # Cline
    ".cline": "Cline",
    ".clinerules": "Cline",
    # Continue
    ".continue/config.json": "Continue",
    ".continue/config.yaml": "Continue",
    ".continue/README.md": "Continue",
    # Windsurf
    ".windsurfrules": "Windsurf",
    # Tabnine
    ".tabnine": "Tabnine",
    # Codeium
    ".codeium": "Codeium",
    # Amazon Q
    ".amazonq": "Amazon Q",
    ".amazonq/rules": "Amazon Q",
}

AI_MODEL_PATTERNS = [
    r"\.pt$",           # PyTorch
    r"\.pth$",          # PyTorch
    r"\.onnx$",         # ONNX
    r"\.h5$",           # HDF5 (Keras)
    r"\.pb$",           # TensorFlow
    r"\.tflite$",       # TensorFlow Lite
    r"\.safetensors$",  # HuggingFace SafeTensors
    r"\.gguf$",         # GGUF (llama.cpp)
    r"\.ggml$",         # GGML
    r"\.bin$",          # Model binary (when paired with config)
    r"\.ckpt$",         # Checkpoint
    r"\.weights$",      # Weights file
    r"\.pkl$",          # Pickle (model)
    r"\.joblib$",       # Joblib (sklearn)
    r"\.npy$",          # NumPy array
    r"\.npz$",          # NumPy compressed
    r"\.arrow$",        # Apache Arrow (datasets)
    r"\.parquet$",      # Parquet (datasets)
    r"tokenizer\.json$", # Tokenizer
    r"tokenizer_config\.json$", # Tokenizer config
    r"vocab\.json$",    # Vocabulary
    r"merges\.txt$",    # BPE merges
]

AI_TRAINING_PATTERNS = [
    r"train(?:ing)?\.py$",
    r"finetune(?:_?\.py)?$",
    r"fine[-_]tune\.py$",
    r"pretrain\.py$",
    r"evaluate\.py$",
    r"eval\.py$",
    r"infer(?:ence)?\.py$",
    r"predict\.py$",
    r"generate\.py$",
    r"sample\.py$",
    r"benchmark\.py$",
    r"dataset\.py$",
    r"data(?:_?loader)?\.py$",
]

AI_DIR_NAMES = {
    "models": "Model Storage",
    "ml": "Machine Learning",
    "ai": "Artificial Intelligence",
    "machine-learning": "Machine Learning",
    "machine_learning": "Machine Learning",
    "deep-learning": "Deep Learning",
    "deep_learning": "Deep Learning",
    "nlp": "Natural Language Processing",
    "cv": "Computer Vision",
    "computer-vision": "Computer Vision",
    "notebooks": "Notebooks",
    "jupyter": "Jupyter Notebooks",
    "data": "Data",
    "datasets": "Datasets",
    "checkpoints": "Checkpoints",
    "weights": "Model Weights",
    "configs": "Configurations",
    "scripts": "Scripts",
    "training": "Training",
    "inference": "Inference",
    "evaluation": "Evaluation",
    "experiments": "Experiments",
    "wandb": "W&B Logging",
    "mlflow": "MLflow",
}

AI_TOPICS = {
    "ai", "artificial-intelligence", "machine-learning", "deep-learning",
    "neural-network", "nlp", "natural-language-processing",
    "computer-vision", "cv", "llm", "large-language-model",
    "gpt", "transformer", "transformers", "bert", "gpt-2", "gpt-3", "gpt-4",
    "stable-diffusion", "diffusion", "generative-ai", "genai",
    "reinforcement-learning", "rl", "rlhf",
    "speech-recognition", "text-to-speech", "tts",
    "object-detection", "image-classification", "segmentation",
    "recommendation-system", "time-series", "anomaly-detection",
    "mlops", "ml-ops", "data-science", "analytics",
    "openai", "langchain", "llamaindex", "huggingface",
    "pytorch", "tensorflow", "keras", "jax",
    "rag", "retrieval-augmented-generation",
    "vector-database", "embeddings",
    "prompt-engineering", "fine-tuning",
    "autonomous-agent", "ai-agent",
}

# ─── 평가 결과 모델 ──────────────────────────────────────────────────────────

@dataclass
class AIScore:
    """AI 활용도 평가 결과"""
    name: str
    score: float          # 0~10
    max_score: float      # 10
    details: str
    sub_items: list = field(default_factory=list)
    evidence: list = field(default_factory=list)  # 감지 근거


@dataclass
class AIUtilizationResult:
    """전체 AI 활용도 평가 결과"""
    total_score: float
    grade: str
    items: list
    summary: str
    ai_level: str  # "None", "Basic", "Moderate", "Advanced", "AI-Native"
    detected_packages: dict
    detected_files: list
    detected_topics: list


# ─── AI 활용도 평가 엔진 ──────────────────────────────────────────────────────

class AIUtilizationEvaluator:
    """GitHub 레포지토리의 AI 활용 수준을 평가"""

    def __init__(self, file_content_fetcher=None):
        self.detected_packages: dict = {}  # {package: category}
        self.detected_files: list = []
        self.detected_topics: list = []
        self.detected_dirs: dict = {}  # {dir: purpose}
        self._fetch_file = file_content_fetcher  # 파일 내용 가져오기 함수

    def evaluate(
        self,
        tree: list,
        languages: dict,
        topics: list,
        repo_data: dict,
    ) -> AIUtilizationResult:
        """전체 AI 활용도 평가"""
        items = []

        # 1. AI/ML 라이브러리 사용
        items.append(self._score_ai_packages(tree, languages))

        # 2. AI 설정 파일
        items.append(self._score_ai_config_files(tree))

        # 3. AI 관련 태그/토픽
        items.append(self._score_ai_topics(topics))

        # 4. AI 모델 파일
        items.append(self._score_ai_model_files(tree))

        # 5. AI 에이전트 프레임워크
        items.append(self._score_ai_agent_frameworks(tree, languages))

        # 6. 학습/추론 스크립트
        items.append(self._score_training_scripts(tree))

        # 7. 노트북/데이터셋
        items.append(self._score_notebooks_datasets(tree))

        # 8. AI 문서화
        items.append(self._score_ai_documentation(tree, repo_data))

        # 종합 점수 계산
        total_score = sum(item.score for item in items) / len(items) if items else 0

        # 등급 결정
        if total_score >= 8:
            grade = "A+"
            ai_level = "AI-Native"
        elif total_score >= 6:
            grade = "A"
            ai_level = "Advanced"
        elif total_score >= 4:
            grade = "B+"
            ai_level = "Moderate"
        elif total_score >= 2:
            grade = "B"
            ai_level = "Basic"
        elif total_score >= 1:
            grade = "C"
            ai_level = "Minimal"
        else:
            grade = "N/A"
            ai_level = "None"

        summary = self._generate_summary(total_score, ai_level, items)

        return AIUtilizationResult(
            total_score=round(total_score, 1),
            grade=grade,
            items=items,
            summary=summary,
            ai_level=ai_level,
            detected_packages=self.detected_packages,
            detected_files=self.detected_files,
            detected_topics=self.detected_topics,
        )

    def _detect_language(self, languages: dict) -> str:
        """주요 언어 감지"""
        if not languages:
            return "python"
        primary = max(languages, key=languages.get).lower()
        if primary in ("typescript", "javascript", "tsx", "jsx"):
            return "javascript"
        elif primary in ("python", "py"):
            return "python"
        elif primary in ("rust", "rs"):
            return "rust"
        elif primary in ("java", "kt"):
            return "java"
        elif primary in ("go", "golang"):
            return "go"
        return "python"  # default

    def _score_ai_packages(self, tree: list, languages: dict) -> AIScore:
        """1. AI/ML 라이브러리 사용 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        lang = self._detect_language(languages)

        # 의존성 파일에서 패키지 추출
        found_packages = {}

        for path in file_paths:
            filename = path.split("/")[-1].lower()

            # requirements.txt
            if filename == "requirements.txt":
                self._parse_requirements_txt(path, file_paths, found_packages, lang)

            # pyproject.toml
            elif filename == "pyproject.toml":
                self._parse_pyproject(path, file_paths, found_packages, lang)

            # setup.py / setup.cfg
            elif filename in ("setup.py", "setup.cfg"):
                self._parse_setup_py(path, file_paths, found_packages, lang)

            # package.json
            elif filename == "package.json":
                self._parse_package_json(path, file_paths, found_packages, lang)

            # Cargo.toml
            elif filename == "cargo.toml":
                self._parse_cargo_toml(path, file_paths, found_packages, lang)

            # go.mod
            elif filename == "go.mod":
                self._parse_go_mod(path, file_paths, found_packages, lang)

            # sub-directory requirements files
            elif "requirements" in filename and filename.endswith(".txt"):
                self._parse_requirements_txt(path, file_paths, found_packages, lang)
            elif "requirements" in filename and filename.endswith(".in"):
                self._parse_requirements_txt(path, file_paths, found_packages, lang)
            elif filename == "poetry.lock":
                pass  # lock files don't need parsing

        self.detected_packages = found_packages

        # 점수 계산
        score = 0.0
        evidence = []

        if found_packages:
            # AI 패키지 수에 따른 점수
            count = len(found_packages)
            score = min(10, count * 1.5)

            # 카테고리별 분포
            categories = set(found_packages.values())
            if len(categories) >= 3:
                score = min(10, score + 1.0)

            # 고급 프레임워크 보너스
            advanced = {"Deep Learning", "LLM Agent", "Generative AI", "AI Agent"}
            if categories & advanced:
                score = min(10, score + 1.5)

            details_parts = []
            for pkg, cat in sorted(found_packages.items()):
                details_parts.append(f"{pkg} ({cat})")
                evidence.append(f"패키지 감지: {pkg} [{cat}]")

            details = f"AI 패키지 {count}개 감지: {', '.join(details_parts[:5])}"
            if count > 5:
                details += f" 외 {count-5}개"
        else:
            details = "AI/ML 관련 패키지 미감지"
            score = 0.0

        return AIScore(
            name="AI/ML 라이브러리 사용",
            score=min(10, round(score, 1)),
            max_score=10,
            details=details,
            sub_items=[],
            evidence=evidence,
        )

    def _fetch_file_content(self, path: str) -> Optional[str]:
        """파일 내용 가져오기 (전체 경로 사용)"""
        if self._fetch_file:
            return self._fetch_file(path)
        return None

    def _parse_requirements_txt(self, filename: str, all_files: list, found: dict, lang: str):
        """requirements.txt 파싱"""
        content = self._fetch_file_content(filename)
        if not content:
            return

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('-'):
                continue
            # 패키지 이름 추출 (==, >=, ~= 등 제거)
            pkg = re.split(r'[>=<~!\[]', line)[0].strip().lower()
            if pkg in AI_PACKAGES.get(lang, {}):
                found[pkg] = AI_PACKAGES[lang][pkg]

    def _parse_pyproject(self, filename: str, all_files: list, found: dict, lang: str):
        """pyproject.toml 파싱"""
        content = self._fetch_file_content(filename)
        if not content:
            return

        # 의존성 섹션 파싱
        in_deps = False
        for line in content.splitlines():
            line = line.strip()
            if line in ('[project.dependencies]', '[tool.poetry.dependencies]', 'dependencies = ['):
                in_deps = True
                continue
            if line.startswith('[') and in_deps:
                in_deps = False
                continue
            if in_deps:
                # 패키지 이름 추출
                pkg = re.split(r'[>=<~!\["\']', line)[0].strip().lower()
                if pkg and pkg in AI_PACKAGES.get(lang, {}):
                    found[pkg] = AI_PACKAGES[lang][pkg]

    def _parse_setup_py(self, filename: str, all_files: list, found: dict, lang: str):
        """setup.py 파싱"""
        content = self._fetch_file_content(filename)
        if not content:
            return

        # install_requires 파싱
        match = re.search(r'install_requires\s*=\s*\[(.*?)\]', content, re.DOTALL)
        if match:
            deps_str = match.group(1)
            for dep in re.split(r'[\',\']', deps_str):
                dep = dep.strip().strip('"').strip("'")
                if dep:
                    pkg = re.split(r'[>=<~!]', dep)[0].strip().lower()
                    if pkg in AI_PACKAGES.get(lang, {}):
                        found[pkg] = AI_PACKAGES[lang][pkg]

    def _parse_package_json(self, filename: str, all_files: list, found: dict, lang: str):
        """package.json 파싱"""
        import json as json_module
        content = self._fetch_file_content(filename)
        if not content:
            return

        try:
            data = json_module.loads(content)
            # dependencies + devDependencies
            for dep_type in ['dependencies', 'devDependencies']:
                deps = data.get(dep_type, {})
                for pkg_name in deps.keys():
                    pkg_lower = pkg_name.lower()
                    if pkg_lower in AI_PACKAGES.get(lang, {}):
                        found[pkg_name] = AI_PACKAGES[lang][pkg_lower]
        except (json_module.JSONDecodeError, KeyError):
            pass

    def _parse_cargo_toml(self, filename: str, all_files: list, found: dict, lang: str):
        """Cargo.toml 파싱"""
        content = self._fetch_file_content(filename)
        if not content:
            return

        in_deps = False
        for line in content.splitlines():
            line = line.strip()
            if line in ('[dependencies]', '[dev-dependencies]', '[build-dependencies]'):
                in_deps = True
                continue
            if line.startswith('[') and in_deps:
                in_deps = False
                continue
            if in_deps and '=' in line:
                pkg = line.split('=')[0].strip().lower()
                if pkg in AI_PACKAGES.get(lang, {}):
                    found[pkg] = AI_PACKAGES[lang][pkg]

    def _parse_go_mod(self, filename: str, all_files: list, found: dict, lang: str):
        """go.mod 파싱"""
        content = self._fetch_file_content(filename)
        if not content:
            return

        in_require = False
        for line in content.splitlines():
            line = line.strip()
            if line.startswith('require ('):
                in_require = True
                continue
            if line == ')' and in_require:
                in_require = False
                continue
            if in_require and line:
                # 모듈 경로에서 패키지 이름 추출
                parts = line.split()
                if parts:
                    mod_path = parts[0]
                    pkg_name = mod_path.split('/')[-1].lower()
                    # Go 모듈 전체 경로도 확인
                    full_mod = mod_path.lower()
                    for ai_pkg, ai_cat in AI_PACKAGES.get(lang, {}).items():
                        if ai_pkg in pkg_name or ai_pkg in full_mod:
                            found[mod_path] = ai_cat

    def _score_ai_config_files(self, tree: list) -> AIScore:
        """2. AI 설정 파일 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        found_configs = {}

        for path in file_paths:
            # 정확한 경로 매칭
            if path in AI_CONFIG_FILES:
                found_configs[path] = AI_CONFIG_FILES[path]
            # 부분 매칭
            for pattern, tool in AI_CONFIG_FILES.items():
                if pattern in path:
                    found_configs[path] = tool
                    break

        score = 0.0
        evidence = []

        if found_configs:
            score = min(10, len(found_configs) * 3.0)

            # 다양한 AI 도구 사용 보너스
            tools = set(found_configs.values())
            if len(tools) >= 2:
                score = min(10, score + 1.0)

            details_parts = []
            for path, tool in sorted(found_configs.items()):
                details_parts.append(f"{tool} ({path})")
                evidence.append(f"AI 설정 파일: {path} [{tool}]")

            details = f"AI 설정 파일 {len(found_configs)}개 감지: {', '.join(details_parts[:3])}"
        else:
            details = "AI 관련 설정 파일 미감지"
            score = 0.0

        return AIScore(
            name="AI 설정 파일",
            score=min(10, round(score, 1)),
            max_score=10,
            details=details,
            sub_items=[],
            evidence=evidence,
        )

    def _score_ai_topics(self, topics: list) -> AIScore:
        """3. AI 관련 태그/토픽 평가"""
        if not topics:
            return AIScore(
                name="AI 관련 태그",
                score=0.0,
                max_score=10,
                details="태그 없음",
                sub_items=[],
                evidence=[],
            )

        topics_lower = [t.lower() for t in topics]
        ai_topics = [t for t in topics_lower if t in AI_TOPICS]

        self.detected_topics = ai_topics

        score = 0.0
        evidence = []

        if ai_topics:
            score = min(10, len(ai_topics) * 2.0)

            details_parts = [f"'{t}'" for t in ai_topics[:5]]
            details = f"AI 관련 태그 {len(ai_topics)}개: {', '.join(details_parts)}"
            evidence = [f"태그 감지: {t}" for t in ai_topics]
        else:
            details = f"AI 관련 태그 없음 (전체 태그: {len(topics)}개)"
            score = 0.0

        return AIScore(
            name="AI 관련 태그",
            score=min(10, round(score, 1)),
            max_score=10,
            details=details,
            sub_items=[],
            evidence=evidence,
        )

    def _score_ai_model_files(self, tree: list) -> AIScore:
        """4. AI 모델 파일 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        model_files = []

        for path in file_paths:
            for pattern in AI_MODEL_PATTERNS:
                if re.search(pattern, path, re.IGNORECASE):
                    model_files.append(path)
                    break

        score = 0.0
        evidence = []

        if model_files:
            # 모델 파일 크기 고려 (총합)
            total_size = sum(
                item.get("size", 0)
                for item in tree
                if item.get("type") == "blob" and item.get("path") in model_files
            )

            count = len(model_files)
            score = min(10, count * 1.0)

            # 대용량 모델 보너스 (100MB+)
            if total_size > 100 * 1024 * 1024:
                score = min(10, score + 2.0)
            elif total_size > 10 * 1024 * 1024:
                score = min(10, score + 1.0)

            details_parts = []
            for f in model_files[:3]:
                ext = f.split(".")[-1]
                details_parts.append(f"{f} (.{ext})")
                evidence.append(f"모델 파일: {f}")

            details = f"AI 모델 파일 {count}개 감지 (총 {total_size/1024/1024:.1f}MB)"
            if count > 3:
                details += f" ({', '.join(details_parts)} 외 {count-3}개)"
            else:
                details += f" ({', '.join(details_parts)})"
        else:
            details = "AI 모델 파일 미감지"
            score = 0.0

        return AIScore(
            name="AI 모델 파일",
            score=min(10, round(score, 1)),
            max_score=10,
            details=details,
            sub_items=[],
            evidence=evidence,
        )

    def _score_ai_agent_frameworks(self, tree: list, languages: dict) -> AIScore:
        """5. AI 에이전트 프레임워크 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        file_names = [p.split("/")[-1].lower() for p in file_paths]

        agent_indicators = []

        # 에이전트 관련 파일 패턴
        agent_file_patterns = {
            "agent.py": "AI Agent",
            "agents.py": "AI Agent",
            "agent_config": "AI Agent",
            "workflow.py": "AI Workflow",
            "pipeline.py": "AI Pipeline",
            "orchestrator.py": "AI Orchestrator",
            "chain.py": "Chain (LangChain)",
            "chain_config": "Chain (LangChain)",
            "prompt.py": "Prompt Management",
            "prompts.py": "Prompt Management",
            "prompt_templates": "Prompt Templates",
            "tool.py": "AI Tool",
            "tools.py": "AI Tools",
            "memory.py": "AI Memory",
            "retriever.py": "RAG Retriever",
            "rag.py": "RAG System",
            "embeddings.py": "Embeddings",
            "vectorstore.py": "Vector Store",
        }

        for fn in file_names:
            for pattern, category in agent_file_patterns.items():
                if pattern in fn:
                    agent_indicators.append((fn, category))
                    break

        score = 0.0
        evidence = []

        if agent_indicators:
            score = min(10, len(agent_indicators) * 2.0)

            details_parts = []
            for fn, cat in agent_indicators[:3]:
                details_parts.append(f"{fn} ({cat})")
                evidence.append(f"에이전트 파일: {fn} [{cat}]")

            details = f"AI 에이전트 구성요소 {len(agent_indicators)}개 감지: {', '.join(details_parts)}"
        else:
            details = "AI 에이전트 관련 파일 미감지"
            score = 0.0

        return AIScore(
            name="AI 에이전트 프레임워크",
            score=min(10, round(score, 1)),
            max_score=10,
            details=details,
            sub_items=[],
            evidence=evidence,
        )

    def _score_training_scripts(self, tree: list) -> AIScore:
        """6. 학습/추론 스크립트 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        training_files = []

        for path in file_paths:
            for pattern in AI_TRAINING_PATTERNS:
                if re.search(pattern, path, re.IGNORECASE):
                    training_files.append(path)
                    break

        score = 0.0
        evidence = []

        if training_files:
            score = min(10, len(training_files) * 1.5)

            # 파이프라인 완성도 보너스
            has_train = any("train" in f.lower() for f in training_files)
            has_eval = any("eval" in f.lower() or "evaluate" in f.lower() for f in training_files)
            has_infer = any("infer" in f.lower() or "predict" in f.lower() for f in training_files)

            if has_train and has_eval:
                score = min(10, score + 1.0)
            if has_train and has_eval and has_infer:
                score = min(10, score + 1.0)

            details_parts = []
            for f in training_files[:3]:
                details_parts.append(f.split("/")[-1])
                evidence.append(f"학습 스크립트: {f}")

            details = f"학습/추론 스크립트 {len(training_files)}개: {', '.join(details_parts)}"
            if len(training_files) > 3:
                details += f" 외 {len(training_files)-3}개"
        else:
            details = "학습/추론 스크립트 미감지"
            score = 0.0

        return AIScore(
            name="학습/추론 스크립트",
            score=min(10, round(score, 1)),
            max_score=10,
            details=details,
            sub_items=[],
            evidence=evidence,
        )

    def _score_notebooks_datasets(self, tree: list) -> AIScore:
        """7. 노트북/데이터셋 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]

        notebooks = [p for p in file_paths if p.endswith(".ipynb")]
        datasets = [p for p in file_paths if any(
            ext in p.lower() for ext in (".csv", ".jsonl", ".parquet", ".arrow", ".feather")
        )]
        data_dirs = set()
        for p in file_paths:
            parts = p.split("/")
            if len(parts) > 1:
                dir_name = parts[0].lower()
                if dir_name in ("data", "datasets", "dataframes", "corpus"):
                    data_dirs.add(dir_name)

        score = 0.0
        evidence = []

        # 노트북
        if notebooks:
            score += min(5, len(notebooks) * 1.0)
            evidence = [f"노트북: {n}" for n in notebooks[:3]]

        # 데이터셋
        if datasets:
            score += min(3, len(datasets) * 0.5)
            evidence += [f"데이터셋: {d}" for d in datasets[:3]]

        # 데이터 디렉토리
        if data_dirs:
            score += min(2, len(data_dirs) * 1.0)
            evidence += [f"데이터 디렉토리: {d}" for d in data_dirs]

        if score > 0:
            details_parts = []
            if notebooks:
                details_parts.append(f"노트북 {len(notebooks)}개")
            if datasets:
                details_parts.append(f"데이터셋 {len(datasets)}개")
            if data_dirs:
                details_parts.append(f"데이터 디렉토리 {len(data_dirs)}개")
            details = " · ".join(details_parts)
        else:
            details = "노트북/데이터셋 미감지"
            score = 0.0

        return AIScore(
            name="노트북/데이터셋",
            score=min(10, round(score, 1)),
            max_score=10,
            details=details,
            sub_items=[],
            evidence=evidence,
        )

    def _score_ai_documentation(self, tree: list, repo_data: dict) -> AIScore:
        """8. AI 문서화 평가"""
        file_paths = [item.get("path", "") for item in tree if item.get("type") == "blob"]
        file_names_lower = [p.split("/")[-1].lower() for p in file_paths]
        dir_names = set()
        for p in file_paths:
            parts = p.split("/")
            if len(parts) > 1:
                dir_names.add(parts[0].lower())

        score = 0.0
        evidence = []

        # AI 관련 문서 파일
        ai_doc_patterns = [
            "model_card.md",
            "model_card.html",
            "model_cards.md",
            "datasheet.md",
            "data_card.md",
            "evaluation.md",
            "benchmarks.md",
            "training.md",
            "training_guide.md",
            "inference.md",
            "deployment.md",
            "prompt_guide.md",
            "prompt_engineering.md",
        ]

        found_docs = []
        for fn in file_names_lower:
            for pattern in ai_doc_patterns:
                if pattern in fn:
                    found_docs.append(fn)
                    break

        # docs/ 내 AI 관련 파일
        docs_dirs = [d for d in dir_names if d in ("docs", "doc", "documentation", "wiki")]
        if docs_dirs:
            score += 2.0
            evidence.append(f"문서 디렉토리: {', '.join(docs_dirs)}")

        # README 내용 (AI 관련 키워드 - 파일 트리에서 추론)
        readme_files = [f for f in file_names_lower if f.startswith("readme")]
        if readme_files:
            score += 1.0

        # 모델 카드
        if any("model_card" in fn for fn in file_names_lower):
            score += 3.0
            evidence.append("모델 카드 문서 감지")

        # 벤치마크 문서
        if any("benchmark" in fn for fn in file_names_lower):
            score += 2.0
            evidence.append("벤치마크 문서 감지")

        # AI 문서 파일
        score += min(2, len(found_docs) * 0.5)
        for doc in found_docs[:3]:
            evidence.append(f"AI 문서: {doc}")

        if score > 0:
            details_parts = []
            if found_docs:
                details_parts.append(f"AI 문서 {len(found_docs)}개")
            if any("model_card" in fn for fn in file_names_lower):
                details_parts.append("모델 카드")
            if any("benchmark" in fn for fn in file_names_lower):
                details_parts.append("벤치마크")
            details = " · ".join(details_parts) if details_parts else "일부 AI 문서화"
        else:
            details = "AI 관련 문서화 미감지"
            score = 0.0

        return AIScore(
            name="AI 문서화",
            score=min(10, round(score, 1)),
            max_score=10,
            details=details,
            sub_items=[],
            evidence=evidence,
        )

    def _generate_summary(self, total_score: float, ai_level: str, items: list) -> str:
        """AI 활용도 요약 생성"""
        strengths = []
        weaknesses = []

        for item in items:
            if item.score >= 7:
                strengths.append(item.name)
            elif item.score <= 3 and item.score > 0:
                weaknesses.append(item.name)

        parts = []
        parts.append(f"AI 활용 수준: {ai_level} ({total_score:.1f}/10)")

        if strengths:
            parts.append(f"강점: {', '.join(strengths)}")
        if weaknesses:
            parts.append(f"개선 가능: {', '.join(weaknesses)}")

        return " | ".join(parts)


# ─── 메인 evaluator에 통합 ──────────────────────────────────────────────────

def integrate_ai_evaluation(evaluator_instance):
    """
    기존 RepoEvaluator에 AI 활용도 평가를 통합합니다.

    사용법:
        evaluator = RepoEvaluator(owner, repo, token)
        evaluator = integrate_ai_evaluation(evaluator)
        result = evaluator.evaluate()
    """
    ai_evaluator = AIUtilizationEvaluator(file_content_fetcher=evaluator_instance.get_file_content)

    # 기존 evaluate 메서드를 래핑
    original_evaluate = evaluator_instance.evaluate

    def enhanced_evaluate() -> dict:
        result = original_evaluate()

        if "error" in result:
            return result

        # AI 활용도 평가 실행
        tree = evaluator_instance.fetch_tree()
        languages = evaluator_instance.fetch_languages()
        topics = evaluator_instance.repo_data.get("topics", [])

        ai_result = ai_evaluator.evaluate(
            tree=tree,
            languages=languages,
            topics=topics,
            repo_data=evaluator_instance.repo_data,
        )

        # 기존 결과에 AI 활용도 카테고리 추가
        from repo_evaluator import CategoryResult, EvalResult

        ai_category = CategoryResult(name="🤖 AI 활용도", weight=0.10)
        ai_category.score = ai_result.total_score

        # AI 하위 항목들을 EvalResult로 변환
        for item in ai_result.items:
            eval_item = EvalResult(
                name=item.name,
                score=item.score,
                max_score=item.max_score,
                details=item.details,
                sub_items=item.sub_items + item.evidence[:3],
            )
            ai_category.items.append(eval_item)

        result["categories"].append(ai_category)

        # AI 활용도 결과 별도 저장
        result["ai_utilization"] = {
            "score": ai_result.total_score,
            "grade": ai_result.grade,
            "level": ai_result.ai_level,
            "summary": ai_result.summary,
            "detected_packages": ai_result.detected_packages,
            "detected_files": ai_result.detected_files[:10],
            "detected_topics": ai_result.detected_topics,
        }

        # 가중치 재조정 (AI 활용도 10% 추가)
        total_weight = sum(cat.weight for cat in result["categories"])
        if total_weight > 0:
            for cat in result["categories"]:
                cat.weight = cat.weight / total_weight * 0.9  # 기존 가중치 90%

            # AI 활용도 가중치 설정
            ai_category.weight = 0.10

        # 총점 재계산
        total_weighted = sum(cat.weighted_score for cat in result["categories"])
        total_weight = sum(cat.weight for cat in result["categories"])
        result["total_score"] = round(total_weighted / total_weight, 1) if total_weight > 0 else 0

        return result

    evaluator_instance.evaluate = enhanced_evaluate
    return evaluator_instance


# ─── CLI 테스트 ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("AI 활용도 평가 모듈 로드 완료")
    print(f"AI 패키지 목록: {sum(len(v) for v in AI_PACKAGES.values())}개")
    print(f"AI 설정 파일 패턴: {len(AI_CONFIG_FILES)}개")
    print(f"AI 모델 패턴: {len(AI_MODEL_PATTERNS)}개")
    print(f"AI 토픽: {len(AI_TOPICS)}개")
