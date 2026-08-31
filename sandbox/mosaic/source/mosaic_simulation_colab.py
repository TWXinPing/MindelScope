import numpy as np
import matplotlib.pyplot as plt

# Super-clean implement of the MOSAIC Model (Wolpert & Kawato, 1998)
# Designed for Google Colab.

class ForwardModel:
    def __init__(self, learning_rate=0.1):
        # We model the system's next velocity: v_{t+1} = v_t + w * u_t (simplified)
        # In free space, w_true = 1/m. In viscous field, the relationship changes.
        # We learn a single parameter representing the inverse mass / transmission gain.
        self.w = 0.5  # Initial guess
        self.lr = learning_rate

    def predict(self, v_t, u_t):
        # Predicts next velocity based on current velocity and motor command
        return v_t + self.w * u_t

    def update(self, v_t, u_t, v_next, responsibility):
        # Gated gradient descent learning
        pred = self.predict(v_t, u_t)
        error = v_next - pred
        # Gradient of prediction w.r.t w is u_t
        grad = u_t
        # Update is gated by responsibility
        self.w += self.lr * responsibility * error * grad


class InverseModel:
    def __init__(self, learning_rate=0.05):
        # The inverse model calculates the feedforward motor command:
        # u_ff = a * (v_desired - v_t)
        self.a = 0.5  # Initial controller parameter (gain)
        self.lr = learning_rate

    def control(self, v_desired, v_t):
        return self.a * (v_desired - v_t)

    def update(self, v_desired, v_t, u_feedback, responsibility):
        # Feedback-Error-Learning (FEL): Gated by responsibility, using feedback command as error
        # Gradient of control w.r.t a is (v_desired - v_t)
        grad = v_desired - v_t
        self.a += self.lr * responsibility * u_feedback * grad


class MOSAICSimulation:
    def __init__(self, num_modules=2, sigma=0.15):
        self.num_modules = num_modules
        self.sigma = sigma  # Variance parameter for responsibility estimator
        self.forward_models = [ForwardModel(learning_rate=0.1) for _ in range(num_modules)]
        self.inverse_models = [InverseModel(learning_rate=0.05) for _ in range(num_modules)]
        
        # Break symmetry slightly to allow competitive learning
        self.forward_models[0].w = 0.3
        self.forward_models[1].w = 0.7
        self.inverse_models[0].a = 0.3
        self.inverse_models[1].a = 0.8

    def run_simulation(self, num_trials=100, steps_per_trial=50):
        # Tracking variables
        history = {
            'trials': [],
            'v_actual': [],
            'v_desired': [],
            'u_total': [],
            'u_ff': [],
            'u_fb': [],
            'responsibilities': [],
            'f_weights': [],
            'i_weights': []
        }

        # Desired trajectory: a simple smooth velocity profile (e.g., bell-shaped)
        t_steps = np.linspace(0, np.pi, steps_per_trial)
        v_profile = np.sin(t_steps)  # Peak velocity of 1.0

        for trial in range(num_trials):
            # Define Environment context
            # Trial 0-30: Free Space (mass = 1.0, friction = 0)
            # Trial 30-70: Viscous Field (mass = 1.0, friction = 2.0 -> harder to accelerate)
            # Trial 70-100: Free Space again (test for memory retention!)
            if 30 <= trial < 70:
                context = 'viscous'
                m = 1.0
                b = 2.5  # Friction coefficient
            else:
                context = 'free'
                m = 1.0
                b = 0.0

            v_t = 0.0  # Reset velocity at trial start
            
            trial_v = []
            trial_resp = []
            trial_uff = []
            trial_ufb = []

            for step in range(steps_per_trial):
                v_des = v_profile[step]
                
                # 1. Generate feedforward command from all inverse models
                u_ff_i = [inv.control(v_des, v_t) for inv in self.inverse_models]
                
                # 2. Responsibility estimation from PREVIOUS step's prediction error
                # On the very first step, split responsibilities 50/50
                if step == 0:
                    resp = np.ones(self.num_modules) / self.num_modules
                else:
                    # Compute prediction errors of forward models
                    # How well did each forward model predict the current v_t from the previous state?
                    errors = []
                    for i in range(self.num_modules):
                        pred_v = self.forward_models[i].predict(prev_v, prev_u)
                        errors.append(v_t - pred_v)
                    
                    # Convert to gaussian likelihood and normalize (Softmax)
                    errors = np.array(errors)
                    likelihoods = np.exp(-(errors**2) / (self.sigma**2))
                    # Prevent division by zero
                    if np.sum(likelihoods) == 0:
                        resp = np.ones(self.num_modules) / self.num_modules
                    else:
                        resp = likelihoods / np.sum(likelihoods)

                # 3. Combine feedforward motor commands using responsibilities
                u_ff_total = np.sum(resp * np.array(u_ff_i))

                # 4. Generate Feedback Command (acting as biological reflex/error corrector)
                # u_fb = K_fb * (v_desired - v_actual)
                k_fb = 1.5
                u_fb = k_fb * (v_des - v_t)

                # Total motor command
                u_total = u_ff_total + u_fb

                # 5. Physics Simulation (Environment)
                # dv/dt = (u - b*v) / m
                dv = (u_total - b * v_t) / m
                v_next = v_t + dv * 0.1  # dt = 0.1
                # Add a little sensory noise
                v_next += np.random.normal(0, 0.02)

                # Record states for learning
                prev_v = v_t
                prev_u = u_total
                v_t = v_next

                # 6. Gated Learning (Forward & Inverse models update using current responsibility)
                for i in range(self.num_modules):
                    # Forward Model learns to predict the actual outcome
                    self.forward_models[i].update(prev_v, prev_u, v_t, resp[i])
                    # Inverse Model learns using Feedback Error Learning (FEL)
                    self.inverse_models[i].update(v_des, prev_v, u_fb, resp[i])

                # Save step history
                trial_v.append(v_t)
                trial_resp.append(resp)
                trial_uff.append(u_ff_total)
                trial_ufb.append(u_fb)

            # Record trial-level metrics (mean of the trial)
            history['trials'].append(trial)
            history['v_actual'].append(np.mean(trial_v))
            history['v_desired'].append(np.mean(v_profile))
            history['responsibilities'].append(np.mean(trial_resp, axis=0))
            history['u_ff'].append(np.mean(trial_uff))
            history['u_fb'].append(np.mean(trial_ufb))
            history['f_weights'].append([f.w for f in self.forward_models])
            history['i_weights'].append([inv.a for inv in self.inverse_models])

        return history


# --- RUN & PLOT ---
sim = MOSAICSimulation()
history = sim.run_simulation(num_trials=100)

# Create a professional diagnostic plot
fig, axes = plt.subplots(3, 1, figsize=(10, 12), sharex=True)

# Plot 1: Responsibility Signals over trials
resp = np.array(history['responsibilities'])
axes[0].plot(resp[:, 0], label='Module 1 Responsibility (Free Space)', color='#1f77b4', linewidth=2.5)
axes[0].plot(resp[:, 1], label='Module 2 Responsibility (Viscous Field)', color='#ff7f0e', linewidth=2.5)
axes[0].axvspan(30, 70, color='gray', alpha=0.15, label='Viscous Field Active (Damping)')
axes[0].set_ylabel('Responsibility ($\\lambda$)', fontsize=12)
axes[0].set_title('MOSAIC Dynamic Module Selection & Responsibility Signals', fontsize=14, fontweight='bold')
axes[0].legend(loc='upper right', frameon=True)
axes[0].grid(True, linestyle='--', alpha=0.6)

# Plot 2: Control contribution (Feedforward vs Feedback)
# As learning progresses, u_fb (feedback error) should drop to 0, and u_ff (feedforward predict) should take over!
axes[1].plot(history['u_ff'], label='Feedforward Command ($u_{ff}$)', color='#2ca02c', linewidth=2)
axes[1].plot(history['u_fb'], label='Feedback Corrective Command ($u_{fb}$)', color='#d62728', linewidth=2)
axes[1].axvspan(30, 70, color='gray', alpha=0.15)
axes[1].set_ylabel('Motor Command Force', fontsize=12)
axes[1].set_title('Feedback-Error-Learning (FEL): Transition from Feedback to Feedforward Control', fontsize=12)
axes[1].legend(loc='upper right')
axes[1].grid(True, linestyle='--', alpha=0.6)

# Plot 3: Internal Model Parameter Evolution
f_w = np.array(history['f_weights'])
axes[2].plot(f_w[:, 0], '--', label='Forward Model 1 Weight ($w_1$)', color='#1f77b4', linewidth=2)
axes[2].plot(f_w[:, 1], '--', label='Forward Model 2 Weight ($w_2$)', color='#ff7f0e', linewidth=2)
axes[2].axvspan(30, 70, color='gray', alpha=0.15)
axes[2].set_xlabel('Trials', fontsize=12)
axes[2].set_ylabel('Model Parameters', fontsize=12)
axes[2].set_title('Cooperative Parameter Evolution (No Interference between Modules)', fontsize=12)
axes[2].legend(loc='upper right')
axes[2].grid(True, linestyle='--', alpha=0.6)

plt.tight_layout()
plt.show()
