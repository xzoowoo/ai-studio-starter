
# AI 스튜디오 (MVP) — Flask 버전

왼쪽은 업로드/옵션/버튼, 오른쪽은 갤러리 구성의 **AI 프로필 이미지 생성기**입니다.
MVP는 Hugging Face Inference API로 **텍스트→이미지**를 생성합니다.
(업로드한 사진은 참고용 저장만 하며, 얼굴 동일성 복제는 다음 단계에서 추가합니다.)

## 1) 설치 (Windows 기준)
```bash
# 1. 파이썬 3.10+ 설치 (이미 설치되어 있다면 건너뛰기)
# 2. 이 폴더에서 가상환경 만들기 (권장)
python -m venv .venv
.venv\Scripts\activate

# 3. 패키지 설치
pip install -r requirements.txt
```

## 2) 환경변수(.env) 설정
`.env.example` 파일을 복사해 `.env`로 이름을 바꾸고, Hugging Face 토큰을 넣어주세요.
```env
HF_TOKEN=hf_xxx_여기에_본인토큰
HF_MODEL=stabilityai/stable-diffusion-2-1
```

## 3) 실행
```bash
python app.py
```
브라우저에서 <http://localhost:5000> 접속.

## 4) 배포(Render 권장)
1. GitHub 저장소에 이 폴더를 그대로 업로드
2. https://render.com → New → Web Service → GitHub 저장소 연결
3. **Build Command**: `pip install -r requirements.txt`
4. **Start Command**: `gunicorn app:app`
5. **Environment** 탭에서 `HF_TOKEN`, `HF_MODEL` 환경변수 추가
6. 배포 완료 후 제공된 URL 접속

## 5) 다음 단계(동일 인물 유지)
- InstantID / IP-Adapter 기반 **이미지-투-이미지** 모델을 백엔드에 추가하면
  업로드한 얼굴을 참고한 결과를 만들 수 있습니다.
- 구현 포인트
  - 업로드 이미지 서버 저장 → 모델 입력으로 전달(모델에 따라 URL 또는 바이트 전송)
  - `/api/generate`에서 텍스트 프롬프트 + 업로드 이미지 동시 사용
  - 결과 저장/갤러리 동일
- 비용/속도/품질을 고려하여 Replicate/FAL/Hugging Face 등 제공처 중 선택하세요.

## 6) 라이선스/안내
- 공개 서비스로 운영 시 **이용약관/개인정보처리방침** 페이지를 준비하세요.
- 생성물 허용 범위(누드/저작권 민감 이미지 등) 정책을 명확히 고지하세요.
