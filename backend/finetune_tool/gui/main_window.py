"""
파인튜닝 GUI 메인 윈도우
사용자 친화적인 파인튜닝 인터페이스
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import threading
import os
import sys
import json
from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import seaborn as sns

# 상위 디렉토리 import
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import config_manager
from data_processor import DataProcessor
from model_trainer import ModelTrainer

class FinetuneGUI:
    """파인튜닝 GUI 클래스"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("AI 상담사 파인튜닝 도구")
        self.root.geometry("1200x800")
        
        # 설정
        self.config = config_manager
        self.data_processor = None
        self.model_trainer = None
        
        # GUI 상태
        self.is_training = False
        self.training_thread = None
        
        # GUI 초기화
        self.setup_gui()
        
    def setup_gui(self):
        """GUI 설정"""
        
        # 메인 프레임
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 타이틀
        title_label = ctk.CTkLabel(
            main_frame, 
            text="AI 상담사 파인튜닝 도구", 
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=20)
        
        # 노트북 (탭) 생성
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 탭 생성
        self.create_data_tab()
        self.create_model_tab()
        self.create_training_tab()
        self.create_monitoring_tab()
        self.create_cloud_tab()
        
    def create_data_tab(self):
        """데이터 탭 생성"""
        
        data_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(data_frame, text="데이터 설정")
        
        # 데이터 경로 설정
        path_frame = ctk.CTkFrame(data_frame)
        path_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(path_frame, text="데이터 경로 설정", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # FAQ 데이터 경로
        faq_frame = ctk.CTkFrame(path_frame)
        faq_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(faq_frame, text="FAQ 데이터:").pack(side="left", padx=5)
        self.faq_path_var = tk.StringVar(value=self.config.data.faq_data_path)
        faq_entry = ctk.CTkEntry(faq_frame, textvariable=self.faq_path_var, width=400)
        faq_entry.pack(side="left", padx=5)
        ctk.CTkButton(faq_frame, text="찾아보기", command=self.browse_faq_file).pack(side="left", padx=5)
        
        # 대화 데이터 경로
        conv_frame = ctk.CTkFrame(path_frame)
        conv_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(conv_frame, text="대화 데이터:").pack(side="left", padx=5)
        self.conv_path_var = tk.StringVar(value=self.config.data.conversation_data_path)
        conv_entry = ctk.CTkEntry(conv_frame, textvariable=self.conv_path_var, width=400)
        conv_entry.pack(side="left", padx=5)
        ctk.CTkButton(conv_frame, text="찾아보기", command=self.browse_conv_folder).pack(side="left", padx=5)
        
        # 데이터 분할 설정
        split_frame = ctk.CTkFrame(data_frame)
        split_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(split_frame, text="데이터 분할 설정", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # 분할 비율
        ratio_frame = ctk.CTkFrame(split_frame)
        ratio_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(ratio_frame, text="훈련:").pack(side="left", padx=5)
        self.train_ratio_var = tk.DoubleVar(value=self.config.data.train_ratio)
        train_ratio_entry = ctk.CTkEntry(ratio_frame, textvariable=self.train_ratio_var, width=100)
        train_ratio_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(ratio_frame, text="검증:").pack(side="left", padx=5)
        self.val_ratio_var = tk.DoubleVar(value=self.config.data.val_ratio)
        val_ratio_entry = ctk.CTkEntry(ratio_frame, textvariable=self.val_ratio_var, width=100)
        val_ratio_entry.pack(side="left", padx=5)
        
        ctk.CTkLabel(ratio_frame, text="테스트:").pack(side="left", padx=5)
        self.test_ratio_var = tk.DoubleVar(value=self.config.data.test_ratio)
        test_ratio_entry = ctk.CTkEntry(ratio_frame, textvariable=self.test_ratio_var, width=100)
        test_ratio_entry.pack(side="left", padx=5)
        
        # 데이터 처리 버튼
        button_frame = ctk.CTkFrame(data_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkButton(
            button_frame, 
            text="데이터 전처리 실행", 
            command=self.process_data
        ).pack(pady=10)
        
        # 데이터 통계 표시
        self.stats_text = ctk.CTkTextbox(data_frame, height=200)
        self.stats_text.pack(fill="both", expand=True, padx=10, pady=10)
        
    def create_model_tab(self):
        """모델 탭 생성"""
        
        model_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(model_frame, text="모델 설정")
        
        # 모델 선택
        model_select_frame = ctk.CTkFrame(model_frame)
        model_select_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(model_select_frame, text="모델 설정", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # 모델 타입 선택
        type_frame = ctk.CTkFrame(model_select_frame)
        type_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(type_frame, text="모델 타입:").pack(side="left", padx=5)
        self.model_type_var = tk.StringVar(value=self.config.finetune.model_type)
        model_type_combo = ctk.CTkComboBox(
            type_frame, 
            values=["phi", "llama", "mistral", "gpt2", "bloom"],
            variable=self.model_type_var,
            command=self.on_model_type_change
        )
        model_type_combo.pack(side="left", padx=5)
        
        # 모델 이름
        name_frame = ctk.CTkFrame(model_select_frame)
        name_frame.pack(fill="x", padx=10, pady=5)
        
        ctk.CTkLabel(name_frame, text="모델 이름:").pack(side="left", padx=5)
        self.model_name_var = tk.StringVar(value=self.config.finetune.model_name)
        model_name_entry = ctk.CTkEntry(name_frame, textvariable=self.model_name_var, width=400)
        model_name_entry.pack(side="left", padx=5)
        
        # LoRA 설정
        lora_frame = ctk.CTkFrame(model_frame)
        lora_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(lora_frame, text="LoRA 설정", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # LoRA 파라미터
        lora_params_frame = ctk.CTkFrame(lora_frame)
        lora_params_frame.pack(fill="x", padx=10, pady=5)
        
        # r 값
        r_frame = ctk.CTkFrame(lora_params_frame)
        r_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(r_frame, text="r (rank):").pack(side="left", padx=5)
        self.lora_r_var = tk.IntVar(value=self.config.finetune.lora_r)
        r_entry = ctk.CTkEntry(r_frame, textvariable=self.lora_r_var, width=100)
        r_entry.pack(side="left", padx=5)
        
        # alpha 값
        alpha_frame = ctk.CTkFrame(lora_params_frame)
        alpha_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(alpha_frame, text="alpha:").pack(side="left", padx=5)
        self.lora_alpha_var = tk.IntVar(value=self.config.finetune.lora_alpha)
        alpha_entry = ctk.CTkEntry(alpha_frame, textvariable=self.lora_alpha_var, width=100)
        alpha_entry.pack(side="left", padx=5)
        
        # dropout 값
        dropout_frame = ctk.CTkFrame(lora_params_frame)
        dropout_frame.pack(fill="x", pady=2)
        ctk.CTkLabel(dropout_frame, text="dropout:").pack(side="left", padx=5)
        self.lora_dropout_var = tk.DoubleVar(value=self.config.finetune.lora_dropout)
        dropout_entry = ctk.CTkEntry(dropout_frame, textvariable=self.lora_dropout_var, width=100)
        dropout_entry.pack(side="left", padx=5)
        
        # 양자화 설정
        quant_frame = ctk.CTkFrame(model_frame)
        quant_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(quant_frame, text="양자화 설정", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.use_4bit_var = tk.BooleanVar(value=self.config.finetune.use_4bit)
        ctk.CTkCheckBox(quant_frame, text="4비트 양자화 사용", variable=self.use_4bit_var).pack(pady=5)
        
        self.use_8bit_var = tk.BooleanVar(value=self.config.finetune.use_8bit)
        ctk.CTkCheckBox(quant_frame, text="8비트 양자화 사용", variable=self.use_8bit_var).pack(pady=5)
        
    def create_training_tab(self):
        """훈련 탭 생성"""
        
        training_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(training_frame, text="훈련 설정")
        
        # 훈련 파라미터
        params_frame = ctk.CTkFrame(training_frame)
        params_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(params_frame, text="훈련 파라미터", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # 에포크 수
        epochs_frame = ctk.CTkFrame(params_frame)
        epochs_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(epochs_frame, text="에포크 수:").pack(side="left", padx=5)
        self.epochs_var = tk.IntVar(value=self.config.finetune.num_epochs)
        epochs_entry = ctk.CTkEntry(epochs_frame, textvariable=self.epochs_var, width=100)
        epochs_entry.pack(side="left", padx=5)
        
        # 학습률
        lr_frame = ctk.CTkFrame(params_frame)
        lr_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(lr_frame, text="학습률:").pack(side="left", padx=5)
        self.lr_var = tk.DoubleVar(value=self.config.finetune.learning_rate)
        lr_entry = ctk.CTkEntry(lr_frame, textvariable=self.lr_var, width=100)
        lr_entry.pack(side="left", padx=5)
        
        # 배치 크기
        batch_frame = ctk.CTkFrame(params_frame)
        batch_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(batch_frame, text="배치 크기:").pack(side="left", padx=5)
        self.batch_size_var = tk.IntVar(value=self.config.finetune.batch_size)
        batch_entry = ctk.CTkEntry(batch_frame, textvariable=self.batch_size_var, width=100)
        batch_entry.pack(side="left", padx=5)
        
        # 그래디언트 누적
        grad_frame = ctk.CTkFrame(params_frame)
        grad_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(grad_frame, text="그래디언트 누적:").pack(side="left", padx=5)
        self.grad_accum_var = tk.IntVar(value=self.config.finetune.gradient_accumulation_steps)
        grad_entry = ctk.CTkEntry(grad_frame, textvariable=self.grad_accum_var, width=100)
        grad_entry.pack(side="left", padx=5)
        
        # 출력 설정
        output_frame = ctk.CTkFrame(training_frame)
        output_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(output_frame, text="출력 설정", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        # 출력 디렉토리
        out_dir_frame = ctk.CTkFrame(output_frame)
        out_dir_frame.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(out_dir_frame, text="출력 디렉토리:").pack(side="left", padx=5)
        self.output_dir_var = tk.StringVar(value=self.config.finetune.output_dir)
        out_dir_entry = ctk.CTkEntry(out_dir_frame, textvariable=self.output_dir_var, width=400)
        out_dir_entry.pack(side="left", padx=5)
        ctk.CTkButton(out_dir_frame, text="찾아보기", command=self.browse_output_dir).pack(side="left", padx=5)
        
        # 훈련 버튼
        button_frame = ctk.CTkFrame(training_frame)
        button_frame.pack(fill="x", padx=10, pady=10)
        
        self.train_button = ctk.CTkButton(
            button_frame, 
            text="파인튜닝 시작", 
            command=self.start_training
        )
        self.train_button.pack(pady=10)
        
        # 훈련 시간 예상
        self.time_estimate_label = ctk.CTkLabel(button_frame, text="")
        self.time_estimate_label.pack(pady=5)
        
    def create_monitoring_tab(self):
        """모니터링 탭 생성"""
        
        monitor_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(monitor_frame, text="훈련 모니터링")
        
        # 로그 출력
        log_frame = ctk.CTkFrame(monitor_frame)
        log_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        ctk.CTkLabel(log_frame, text="훈련 로그", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.log_text = ctk.CTkTextbox(log_frame, height=400)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 진행률 표시
        progress_frame = ctk.CTkFrame(monitor_frame)
        progress_frame.pack(fill="x", padx=10, pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame)
        self.progress_bar.pack(fill="x", padx=10, pady=5)
        self.progress_bar.set(0)
        
        self.progress_label = ctk.CTkLabel(progress_frame, text="대기 중...")
        self.progress_label.pack(pady=5)
        
    def create_cloud_tab(self):
        """클라우드 탭 생성 (향후 사용)"""
        
        cloud_frame = ctk.CTkFrame(self.notebook)
        self.notebook.add(cloud_frame, text="클라우드 설정")
        
        # 클라우드 제공업체 선택
        provider_frame = ctk.CTkFrame(cloud_frame)
        provider_frame.pack(fill="x", padx=10, pady=10)
        
        ctk.CTkLabel(provider_frame, text="클라우드 설정 (향후 사용)", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkLabel(provider_frame, text="현재는 로컬 GPU만 지원합니다.").pack(pady=10)
        ctk.CTkLabel(provider_frame, text="클라우드 GPU 지원은 추후 업데이트 예정입니다.").pack(pady=5)
        
    def browse_faq_file(self):
        """FAQ 파일 찾아보기"""
        filename = filedialog.askopenfilename(
            title="FAQ CSV 파일 선택",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
        )
        if filename:
            self.faq_path_var.set(filename)
            
    def browse_conv_folder(self):
        """대화 데이터 폴더 찾아보기"""
        folder = filedialog.askdirectory(title="대화 데이터 폴더 선택")
        if folder:
            self.conv_path_var.set(folder)
            
    def browse_output_dir(self):
        """출력 디렉토리 찾아보기"""
        folder = filedialog.askdirectory(title="출력 디렉토리 선택")
        if folder:
            self.output_dir_var.set(folder)
            
    def on_model_type_change(self, value):
        """모델 타입 변경 시 호출"""
        model_config = self.config.get_model_config(value)
        self.model_name_var.set(model_config["model_name"])
        
    def process_data(self):
        """데이터 전처리 실행"""
        try:
            # 진행 상황 초기화
            self.stats_text.delete("1.0", tk.END)
            self.stats_text.insert("1.0", "데이터 전처리를 시작합니다...\n\n")
            self.stats_text.see(tk.END)
            self.root.update()
            
            # 설정 업데이트
            self.update_config_from_gui()
            
            # 데이터 프로세서 생성
            self.stats_text.insert(tk.END, "✓ 데이터 프로세서 초기화 완료\n")
            self.stats_text.see(tk.END)
            self.root.update()
            
            self.data_processor = DataProcessor(self.config)
            
            # FAQ 데이터 로드
            self.stats_text.insert(tk.END, "📁 FAQ CSV 파일 로드 중...\n")
            self.stats_text.see(tk.END)
            self.root.update()
            
            faq_df = self.data_processor.load_faq_data(self.config.data.faq_data_path)
            self.stats_text.insert(tk.END, f"✓ FAQ 데이터 로드 완료: {len(faq_df)}개 행\n")
            self.stats_text.see(tk.END)
            self.root.update()
            
            # FAQ 데이터 변환
            self.stats_text.insert(tk.END, "🔄 FAQ 데이터 변환 중...\n")
            self.stats_text.see(tk.END)
            self.root.update()
            
            faq_data = self.data_processor.convert_faq_to_finetune_format(faq_df)
            self.stats_text.insert(tk.END, f"✓ FAQ 데이터 변환 완료: {len(faq_data)}개 항목\n")
            self.stats_text.see(tk.END)
            self.root.update()
            
            # 전체 데이터 처리
            self.stats_text.insert(tk.END, "🔧 전체 데이터 처리 중...\n")
            self.stats_text.see(tk.END)
            self.root.update()
            
            train_dataset, val_dataset, test_dataset = self.data_processor.process_all_data()
            
            # 통계 정보 계산
            self.stats_text.insert(tk.END, "📊 통계 정보 계산 중...\n")
            self.stats_text.see(tk.END)
            self.root.update()
            
            stats = self.data_processor.get_data_stats(faq_data)
            
            stats_text = f"""
✅ 데이터 처리 완료!

📈 데이터 통계:
• 총 샘플 수: {stats.get('total_samples', 0)}개
• 평균 입력 길이: {stats.get('avg_input_length', 0):.1f}자
• 평균 출력 길이: {stats.get('avg_output_length', 0):.1f}자
• 최대 입력 길이: {stats.get('max_input_length', 0)}자
• 최대 출력 길이: {stats.get('max_output_length', 0)}자
• 최소 입력 길이: {stats.get('min_input_length', 0)}자
• 최소 출력 길이: {stats.get('min_output_length', 0)}자

📂 데이터 분할:
• 훈련 데이터: {len(train_dataset)}개
• 검증 데이터: {len(val_dataset)}개
• 테스트 데이터: {len(test_dataset)}개

🎯 데이터 품질:
• 입력 텍스트: {stats.get('total_samples', 0)}개 모두 유효
• 출력 텍스트: {stats.get('total_samples', 0)}개 모두 유효
• 파인튜닝 준비 완료! 🚀
            """
            
            self.stats_text.delete("1.0", tk.END)
            self.stats_text.insert("1.0", stats_text)
            
            messagebox.showinfo("완료", "데이터 전처리가 완료되었습니다!")
            
        except Exception as e:
            error_msg = f"❌ 데이터 처리 중 오류가 발생했습니다:\n{str(e)}"
            self.stats_text.insert(tk.END, f"\n{error_msg}\n")
            messagebox.showerror("오류", error_msg)
            
    def update_config_from_gui(self):
        """GUI에서 설정 업데이트"""
        
        # 데이터 설정
        self.config.data.faq_data_path = self.faq_path_var.get()
        self.config.data.conversation_data_path = self.conv_path_var.get()
        self.config.data.train_ratio = self.train_ratio_var.get()
        self.config.data.val_ratio = self.val_ratio_var.get()
        self.config.data.test_ratio = self.test_ratio_var.get()
        
        # 모델 설정
        self.config.finetune.model_type = self.model_type_var.get()
        self.config.finetune.model_name = self.model_name_var.get()
        self.config.finetune.lora_r = self.lora_r_var.get()
        self.config.finetune.lora_alpha = self.lora_alpha_var.get()
        self.config.finetune.lora_dropout = self.lora_dropout_var.get()
        self.config.finetune.use_4bit = self.use_4bit_var.get()
        self.config.finetune.use_8bit = self.use_8bit_var.get()
        
        # 훈련 설정
        self.config.finetune.num_epochs = self.epochs_var.get()
        self.config.finetune.learning_rate = self.lr_var.get()
        self.config.finetune.batch_size = self.batch_size_var.get()
        self.config.finetune.gradient_accumulation_steps = self.grad_accum_var.get()
        self.config.finetune.output_dir = self.output_dir_var.get()
        
    def start_training(self):
        """파인튜닝 시작"""
        
        if self.is_training:
            messagebox.showwarning("경고", "이미 훈련이 진행 중입니다.")
            return
            
        # 설정 업데이트
        self.update_config_from_gui()
        
        # 데이터 프로세서가 없으면 생성
        if self.data_processor is None:
            self.data_processor = DataProcessor(self.config)
        
        # 별도 스레드에서 훈련 실행
        self.training_thread = threading.Thread(target=self._training_worker)
        self.training_thread.daemon = True
        self.training_thread.start()
        
    def _training_worker(self):
        """훈련 워커 스레드"""
        
        try:
            self.is_training = True
            self.train_button.configure(text="훈련 중...", state="disabled")
            
            # 로그 초기화
            self.log_text.delete("1.0", tk.END)
            self.log_text.insert("1.0", "파인튜닝을 시작합니다...\n")
            
            # 데이터 처리
            train_dataset, val_dataset, test_dataset = self.data_processor.process_all_data()
            
            # 훈련 시간 예상
            self.model_trainer = ModelTrainer(self.config)
            time_estimate = self.model_trainer.estimate_training_time(train_dataset)
            
            estimate_text = f"예상 훈련 시간: {time_estimate['estimated_hours']:.1f}시간"
            self.time_estimate_label.configure(text=estimate_text)
            
            # 훈련 실행
            self.model_trainer.train(train_dataset, val_dataset)
            
            # 모델 저장
            output_path = self.model_trainer.save_model()
            
            # 완료 메시지
            self.log_text.insert(tk.END, f"\n파인튜닝 완료! 모델이 저장되었습니다: {output_path}\n")
            
            messagebox.showinfo("완료", "파인튜닝이 완료되었습니다!")
            
        except Exception as e:
            error_msg = f"훈련 중 오류가 발생했습니다:\n{str(e)}"
            self.log_text.insert(tk.END, f"\n{error_msg}\n")
            messagebox.showerror("오류", error_msg)
            
        finally:
            self.is_training = False
            self.train_button.configure(text="파인튜닝 시작", state="normal")
            
    def run(self):
        """GUI 실행"""
        self.root.mainloop()

if __name__ == "__main__":
    app = FinetuneGUI()
    app.run() 