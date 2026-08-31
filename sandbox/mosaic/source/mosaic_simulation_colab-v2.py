import numpy as np
import matplotlib.pyplot as plt

# =====================================================================
# MOSAIC Model Simulation with Adjustable Sensory Feedback Delay
# Based on Wolpert & Kawato (1998)
# Designed for Google Colab / Jupyter Notebooks (Version 2)
# =====================================================================

class ForwardModel:
    """前向模型 (Forward Model): 預測運動指令產生的物理結果"""
    def __init__(self, learning_rate=0.05, initial_w=0.5):
        self.w = initial_w  # 預測參數 (例如逆質量 1/m)
        self.lr = learning_rate

    def predict(self, v_t, u_t):
        # 限制預測值的物理範圍，防止數值爆炸
        return np.clip(v_t + self.w * u_t, -10.0, 10.0)

    def update(self, v_t, u_t, v_next, responsibility):
        pred = self.predict(v_t, u_t)
        error = np.clip(v_next - pred, -2.0, 2.0)
        grad = np.clip(u_t, -5.0, 5.0)
        # 門控學習
        self.w += self.lr * responsibility * error * grad
        self.w = np.clip(self.w, 0.01, 2.0)  # 物理參數限制為正數


class InverseModel:
    """逆向模型/控制器 (Inverse Model): 計算 Feedforward 運動指令"""
    def __init__(self, learning_rate=0.02, initial_a=0.5):
        self.a = initial_a  # 控制增益 (Controller Gain)
        self.lr = learning_rate

    def control(self, v_desired, v_t):
        return self.a * (v_desired - v_t)

    def update(self, v_desired, v_t, u_feedback, responsibility):
        grad = v_desired - v_t
        self.a += self.lr * responsibility * u_feedback * grad
        self.a = np.clip(self.a, 0.01, 2.0)


class MOSAICSimulation:
    def __init__(self, num_modules=2, sigma=0.15, feedback_delay=0):
        """
        feedback_delay: 延遲的時間步數 (0=無延遲，1=100ms, 2=200ms)
        """
        self.num_modules = num_modules
        self.sigma = sigma
        self.delay = feedback_delay  # 延遲步數
        
        # 初始化兩個模組，打散初始權重以利競爭學習
        self.forward_models = [ForwardModel(learning_rate=0.08, initial_w=0.3),
                               ForwardModel(learning_rate=0.08, initial_w=0.7)]
        self.inverse_models = [InverseModel(learning_rate=0.03, initial_a=0.3),
                               InverseModel(learning_rate=0.03, initial_a=0.8)]

    def run_simulation(self, num_trials=100, steps_per_trial=50):
        history = {
            'trials': [], 'v_actual': [], 'v_desired': [],
            'u_ff': [], 'u_fb': [], 'responsibilities': [],
            'f_weights': [], 'i_weights': []
        }

        t_steps = np.linspace(0, np.pi, steps_per_trial)
        v_profile = np.sin(t_steps)

        for trial in range(num_trials):
            if 30 <= trial < 70:
                m, b = 1.0, 2.5  # 黏滯力場
            else:
                m, b = 1.0, 0.0  # 自由空間

            v_t = 0.0
            
            # 用於儲存歷史軌跡以模擬延遲
            v_history = [0.0]
            u_history = [0.0]
            
            trial_v, trial_resp, trial_uff, trial_ufb = [], [], [], []

            for step in range(steps_per_trial):
                v_des = v_profile[step]
                
                # --- 模擬延遲對齊 (Delay Box Alignment) ---
                delayed_step = step - self.delay
                
                if delayed_step < 0:
                    v_delayed = 0.0
                else:
                    v_delayed = v_history[delayed_step]

                # 1. 前饋指令計算
                u_ff_i = [inv.control(v_des, v_delayed) for inv in self.inverse_models]

                # 2. 責任訊號計算 (包含延遲比對)
                if step == 0:
                    resp = np.ones(self.num_modules) / self.num_modules
                else:
                    if delayed_step <= 0:
                        resp = np.ones(self.num_modules) / self.num_modules
                    else:
                        errors = []
                        prev_v_delayed = v_history[delayed_step - 1]
                        prev_u_delayed = u_history[delayed_step - 1]
                        
                        for i in range(self.num_modules):
                            pred_v = self.forward_models[i].predict(prev_v_delayed, prev_u_delayed)
                            errors.append(v_delayed - pred_v)
                        
                        errors = np.array(errors)
                        likelihoods = np.exp(-(errors**2) / (self.sigma**2))
                        
                        if np.sum(likelihoods) == 0:
                            resp = np.ones(self.num_modules) / self.num_modules
                        else:
                            resp = likelihoods / np.sum(likelihoods)

                # 3. 混合前饋指令
                u_ff_total = np.sum(resp * np.array(u_ff_i))

                # 4. 回饋控制指令 (調降回饋增益 k_fb 至 0.8 以防止延遲下發生無限發散)
                k_fb = 0.8
                u_fb = k_fb * (v_des - v_delayed)

                # 總指令
                u_total = u_ff_total + u_fb
                # 限制指令範圍
                u_total = np.clip(u_total, -10.0, 10.0)

                # 5. 物理環境模擬
                dv = (u_total - b * v_t) / m
                v_next = v_t + dv * 0.1
                v_next = np.clip(v_next + np.random.normal(0, 0.01), -5.0, 5.0)

                # 更新實際物理狀態與暫存器
                v_t = v_next
                v_history.append(v_t)
                u_history.append(u_total)

                # 6. 門控學習更新 (對齊延遲)
                if delayed_step > 0:
                    prev_v_delayed = v_history[delayed_step - 1]
                    prev_u_delayed = u_history[delayed_step - 1]
                    for i in range(self.num_modules):
                        self.forward_models[i].update(prev_v_delayed, prev_u_delayed, v_delayed, resp[i])
                        self.inverse_models[i].update(v_des, v_delayed, u_fb, resp[i])

                trial_v.append(v_t)
                trial_resp.append(resp)
                trial_uff.append(u_ff_total)
                trial_ufb.append(u_fb)

            # 記錄 Trial 數據
            history['trials'].append(trial)
            history['v_actual'].append(np.mean(trial_v))
            history['v_desired'].append(np.mean(v_profile))
            history['responsibilities'].append(np.mean(trial_resp, axis=0))
            history['u_ff'].append(np.mean(trial_uff))
            history['u_fb'].append(np.mean(trial_ufb))
            history['f_weights'].append([f.w for f in self.forward_models])
            history['i_weights'].append([inv.a for inv in self.inverse_models])

        return history


# =====================================================================
# 比較不同延遲下的系統行為並繪製圖表
# =====================================================================

print("正在運行無延遲模擬 (Delay = 0)...")
sim_no_delay = MOSAICSimulation(feedback_delay=0)
hist_no_delay = sim_no_delay.run_simulation(num_trials=100)

print("正在運行中度延遲模擬 (Delay = 1 Step, 100 ms)...")
sim_mid_delay = MOSAICSimulation(feedback_delay=1)
hist_mid_delay = sim_mid_delay.run_simulation(num_trials=100)

print("正在運行重度延遲模擬 (Delay = 2 Steps, 200 ms)...")
sim_high_delay = MOSAICSimulation(feedback_delay=2)
hist_high_delay = sim_high_delay.run_simulation(num_trials=100)

# ── 繪圖 ──
fig, axes = plt.subplots(3, 1, figsize=(12, 14))

# 圖 1: 責任訊號對比
resp_no = np.array(hist_no_delay['responsibilities'])
resp_mid = np.array(hist_mid_delay['responsibilities'])
resp_high = np.array(hist_high_delay['responsibilities'])

axes[0].plot(resp_no[:, 1], label='Delay = 0 (No Delay)', color='#2ca02c', linewidth=2.5)
axes[0].plot(resp_mid[:, 1], label='Delay = 1 Step (100ms)', color='#ff7f0e', linewidth=2.5)
axes[0].plot(resp_high[:, 1], label='Delay = 2 Steps (200ms)', color='#d62728', linewidth=2.5)
axes[0].axvspan(30, 70, color='gray', alpha=0.1, label='Viscous Field Active (Trials 30-70)')
axes[0].set_ylabel(r'Responsibility of Module 2 ($\lambda^2$)', fontsize=12)
axes[0].set_title('Effect of Feedback Delay on Module Selection (Responsibility Lag)', fontsize=14, fontweight='bold')
axes[0].legend(loc='upper right')
axes[0].grid(True, linestyle='--', alpha=0.5)

# 圖 2: 回饋指令震盪對比
axes[1].plot(hist_no_delay['u_fb'], label='Delay = 0 (No Delay)', color='#2ca02c', linewidth=2)
axes[1].plot(hist_mid_delay['u_fb'], label='Delay = 1 Step (100ms)', color='#ff7f0e', linewidth=2)
axes[1].plot(hist_high_delay['u_fb'], label='Delay = 2 Steps (200ms)', color='#d62728', linewidth=2)
axes[1].axvspan(30, 70, color='gray', alpha=0.1)
axes[1].set_ylabel('Feedback Corrective Force ($u_{fb}$)', fontsize=12)
axes[1].set_title('Feedback Instability & Oscillations caused by Delay', fontsize=12)
axes[1].legend(loc='upper right')
axes[1].grid(True, linestyle='--', alpha=0.5)

# 圖 3: 模組 2 參數演化對比
axes[2].plot(np.array(hist_no_delay['f_weights'])[:, 1], label='Delay = 0 (No Delay)', color='#2ca02c', linewidth=2)
axes[2].plot(np.array(hist_mid_delay['f_weights'])[:, 1], label='Delay = 1 Step (100ms)', color='#ff7f0e', linewidth=2)
axes[2].plot(np.array(hist_high_delay['f_weights'])[:, 1], label='Delay = 2 Steps (200ms)', color='#d62728', linewidth=2)
axes[2].axvspan(30, 70, color='gray', alpha=0.1)
axes[2].set_xlabel('Trials', fontsize=12)
axes[2].set_ylabel('Forward Model 2 Parameter ($w_2$)', fontsize=12)
axes[2].set_title('Degradation of Gated Learning Accuracy', fontsize=12)
axes[2].legend(loc='upper right')
axes[2].grid(True, linestyle='--', alpha=0.5)

plt.tight_layout()
plt.show()
