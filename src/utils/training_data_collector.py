"""
학습 데이터 수집 모듈
PDF 처리 결과와 사용자 수정 내용을 학습 데이터로 저장
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, List


class TrainingDataCollector:
    """학습 데이터 수집 및 관리"""

    def __init__(self, data_dir: str = "training_data"):
        """
        Args:
            data_dir: 학습 데이터를 저장할 디렉토리
        """
        self.data_dir = data_dir
        self.data_file = os.path.join(data_dir, "corrections.jsonl")

        # 디렉토리 생성
        os.makedirs(data_dir, exist_ok=True)

    def save_correction(self, original_text: str, corrected_data: Dict[str, Any],
                       source_file: str = None, page_number: int = None):
        """
        수정 내역을 학습 데이터로 저장

        Args:
            original_text: PDF에서 추출한 원본 텍스트
            corrected_data: 사용자가 수정한 데이터 (title, checklist 등)
            source_file: 원본 PDF 파일 경로
            page_number: 페이지 번호
        """
        correction = {
            "timestamp": datetime.now().isoformat(),
            "source_file": source_file,
            "page_number": page_number,
            "original": original_text,
            "corrected": corrected_data
        }

        # JSONL 형식으로 추가 저장
        with open(self.data_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(correction, ensure_ascii=False) + '\n')

        print(f"✅ 학습 데이터 저장됨: {self.data_file}")

    def save_toggle_as_training_data(self, toggle_item, original_pdf_path: str = None):
        """
        토글 아이템 전체를 학습 데이터로 저장

        Args:
            toggle_item: ToggleItem 객체
            original_pdf_path: 원본 PDF 경로
        """
        # 토글 데이터를 딕셔너리로 변환
        toggle_dict = toggle_item.to_dict()

        # 체크리스트 추출
        checklist_texts = [item['text'] for item in toggle_dict.get('checklist', [])]

        corrected_data = {
            "title": toggle_dict.get('title', ''),
            "content": toggle_dict.get('content', ''),
            "checklist": checklist_texts,
            "checklist_count": len(checklist_texts)
        }

        # 원본 텍스트 (체크리스트를 한 줄로 합침)
        original_text = toggle_dict.get('content', '') + '\n' + '\n'.join(checklist_texts)

        self.save_correction(
            original_text=original_text,
            corrected_data=corrected_data,
            source_file=original_pdf_path
        )

    def get_statistics(self) -> Dict[str, Any]:
        """
        저장된 학습 데이터 통계 반환

        Returns:
            Dict: 통계 정보
        """
        if not os.path.exists(self.data_file):
            return {
                "total_corrections": 0,
                "files": []
            }

        corrections = []
        with open(self.data_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    corrections.append(json.loads(line))

        # 파일별 통계
        files = {}
        for corr in corrections:
            source = corr.get('source_file', 'Unknown')
            files[source] = files.get(source, 0) + 1

        return {
            "total_corrections": len(corrections),
            "files": [{"name": k, "count": v} for k, v in files.items()],
            "latest": corrections[-1] if corrections else None
        }

    def export_for_openai_finetuning(self, output_file: str = None) -> str:
        """
        OpenAI 파인튜닝 형식으로 내보내기

        Args:
            output_file: 출력 파일 경로

        Returns:
            str: 생성된 파일 경로
        """
        if output_file is None:
            output_file = os.path.join(self.data_dir, f"openai_finetuning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")

        if not os.path.exists(self.data_file):
            print("⚠️ 학습 데이터가 없습니다")
            return None

        # OpenAI 형식으로 변환
        with open(self.data_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:

            for line in infile:
                if not line.strip():
                    continue

                correction = json.loads(line)
                original = correction.get('original', '')
                corrected = correction.get('corrected', {})

                # OpenAI 파인튜닝 형식
                openai_format = {
                    "messages": [
                        {
                            "role": "system",
                            "content": "당신은 PDF 문서에서 체크리스트를 추출하는 전문가입니다."
                        },
                        {
                            "role": "user",
                            "content": f"다음 텍스트에서 체크리스트를 추출하세요:\n\n{original}"
                        },
                        {
                            "role": "assistant",
                            "content": json.dumps(corrected, ensure_ascii=False)
                        }
                    ]
                }

                outfile.write(json.dumps(openai_format, ensure_ascii=False) + '\n')

        print(f"✅ OpenAI 파인튜닝 파일 생성: {output_file}")
        return output_file

    def export_for_local_finetuning(self, output_file: str = None) -> str:
        """
        로컬 파인튜닝 형식으로 내보내기 (입력-출력 쌍)

        Args:
            output_file: 출력 파일 경로

        Returns:
            str: 생성된 파일 경로
        """
        if output_file is None:
            output_file = os.path.join(self.data_dir, f"local_finetuning_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jsonl")

        if not os.path.exists(self.data_file):
            print("⚠️ 학습 데이터가 없습니다")
            return None

        # 로컬 파인튜닝 형식으로 변환
        with open(self.data_file, 'r', encoding='utf-8') as infile, \
             open(output_file, 'w', encoding='utf-8') as outfile:

            for line in infile:
                if not line.strip():
                    continue

                correction = json.loads(line)
                original = correction.get('original', '')
                corrected = correction.get('corrected', {})

                # 입력-출력 쌍
                local_format = {
                    "input": original,
                    "output": corrected
                }

                outfile.write(json.dumps(local_format, ensure_ascii=False) + '\n')

        print(f"✅ 로컬 파인튜닝 파일 생성: {output_file}")
        return output_file
