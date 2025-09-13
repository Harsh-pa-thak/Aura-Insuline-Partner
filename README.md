## Step 1: Start Your Main Server
This is the most important step. You are no longer running any temporary test files. You are running the final application.
Make sure your virtual environment is activated (source .venv/bin/activate).
In your terminal, from the aura-backend directory, run the main app.py file:
code
```bash
python app.py
```
You should see all the "Loading model..." and "Initializing..." messages, followed by a line confirming the server is running on port 5000.
code
```Code
* Running on http://127.0.0.1:5000
```
Your backend is now live and waiting.
## Step 2: Use curl to Act Like the Frontend
Open a new, separate terminal window. (Do not close the one where the server is running).
This new terminal is your "testing ground." You will send different curl commands to see how the AI core responds to different user inputs.
Here are a few scenarios to test.
Test Case 1: A Simple Meal
Goal: See if the NLP, prediction, and recommendation work for a standard meal.
Run this command:
code
```Bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "message": "I am having a sandwich and an apple for lunch"
      }' \
  http://127.0.0.1:5000/api/chat
```
What to look for in the response:
parsed_info.carbs should be around 55.
dose_recommendation should give a reasonable dose for that carb amount.
glucose_prediction.adjusted_prediction should show a gentle rise in glucose.
Test Case 2: A Meal with Exercise
Goal: Verify that the "hybrid" model logic is working and that the exercise context is being used.
Run this command:
code
```Bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "message": "just ate a bowl of pasta and am going for a 45 minute walk"
      }' \
  http://127.0.0.1:5000/api/chat
```
What to look for in the response:
parsed_info should detect both "pasta" and "walk".
dose_recommendation.reasoning should include the phrase "Adjusted for recent exercise."
contextual_advice.exercise_reduction should be true.
glucose_prediction.adjusted_prediction should show a much flatter curve than a meal alone would.
Test Case 3: An Explicit Carb Amount
Goal: Check if the NLP correctly prioritizes a user's specific carb count.
Run this command:
code
Bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "message": "dinner was about 80g of carbs"
      }' \
  http://127.0.0.1:5000/api/chat
What to look for in the response:
parsed_info.carbs should be exactly 80.
parsed_info.warnings should contain the message: "Used explicit carb amount, ignoring food estimates".
Test Case 4: Just an Activity
Goal: Ensure the system handles non-meal logs gracefully.
Run this command:
code
Bash
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
        "message": "finished a tough workout at the gym"
      }' \
  http://127.0.0.1:5000/api/chat
What to look for in the response:
parsed_info.carbs should be 0.
parsed_info.activities_detected should correctly identify the "gym" workout.
dose_recommendation.recommended_dose should likely be 0.0.
# 🌟 Project Aura: The Ultimate Diabetes Command Center

> *A responsive web application that transforms the daily cognitive burden of diabetes into a proactive, predictive, and seamless experience*

[![Status](https://img.shields.io/badge/Status-In%20Development-orange?style=for-the-badge)](https://github.com/your-repo/project-aura)
[![Web App](https://img.shields.io/badge/Platform-Web%20App-brightgreen?style=for-the-badge)](https://github.com/your-repo/project-aura)
[![AI Powered](https://img.shields.io/badge/AI-Powered-blue?style=for-the-badge)](https://github.com/your-repo/project-aura)
[![100% Free Stack](https://img.shields.io/badge/Stack-100%25%20Free-gold?style=for-the-badge)](https://github.com/your-repo/project-aura)

---

## 🎯 Visi

**Project Aura is the ultimate command center for diabetes management.** Accessible from any browser on any device, it transforms the daily cognitive burden of diabetes into a proactive, predictive, and seamless experience. By centralizing data, forecasting future trends, and providing personalized AI-driven insights, Aura empowers users to take control of their health with confidence and clarity.

---

## ✨ Core Features

### 🧠 **Intelligent Prediction Engine**
- **Glucose Forecasting**: LSTM-powered predictions showing where glucose levels are headed in the next 1-2 hours
- **Visual Future Mapping**: Dual-line charts showing historical (solid) and predicted (dashed) glucose trends
- **Target Range Visualization**: Green background zones highlighting optimal glucose ranges (70-180 mg/dL)

### 🎯 **Personalized AI Dosing**
- **Reinforcement Learning Agent**: Trained in simglucose environment to learn optimal dosing strategies
- **Instant Recommendations**: Enter carbs → Get AI-powered dose suggestion in seconds
- **Safety First**: Deep Q-Network trained with reward functions that heavily penalize dangerous lows

### 🌐 **Universal Accessibility**
- **Any Device, Any Browser**: Responsive web design works on desktop, tablet, and mobile
- **No Installation Required**: Access your diabetes command center from anywhere
- **Progressive Web App**: Fast, reliable performance with offline capabilities

### 📊 **Professional Data Visualization**
- **Interactive Charts**: Built with Recharts for smooth, beautiful data exploration
- **Real-time Updates**: Live data synchronization across all connected devices
- **Clean Interface**: Material-UI components for a polished, medical-grade appearance

---

## 🏗️ Architecture (100% Free Stack)

### Technology Stack

#### **Frontend (Lightning Fast & Beautiful)**
```
⚛️ React + Vite (Ultra-fast development)
🎨 Material-UI (MUI) - Professional design system
📊 Recharts - Interactive data visualizations
🔗 Axios - API communication
🗃️ Zustand - Simple, powerful state management
🌐 Progressive Web App capabilities
```

#### **Backend (Robust & Intelligent)**
```
🐍 Python + Flask/FastAPI
🧠 TensorFlow/Keras (LSTM predictions)
🤖 Stable-Baselines3 (DQN reinforcement learning)
🔬 simglucose (Diabetes simulation environment)
⏰ TimescaleDB extension (Time-series optimization)
```

#### **Database & Deployment (Enterprise-Grade, Zero Cost)**
```
🗄️ PostgreSQL + TimescaleDB
☁️ Vercel (Frontend hosting)
🚀 Render (Backend + Database hosting)
🔄 GitHub Actions (CI/CD pipeline)
```

---

## 🚀 Quick Start

### Prerequisites
```bash
# Backend Requirements
Python 3.8+
PostgreSQL 12+ (or use Render's managed database)

# Frontend Requirements  
Node.js 16+
Modern web browser
```

### Installation

#### 1. Clone the Repository
```bash
git clone https://github.com/your-repo/project-aura.git
cd project-aura
```

#### 2. Backend Setup
```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Setup database (local development)
flask db upgrade

# Generate mock data for development
python scripts/generate_mock_data.py

# Start the development server
flask run --debug
```

#### 3. Frontend Setup
```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Your app will be available at http://localhost:5173
```

#### 4. Production Deployment

**Frontend (Vercel):**
```bash
# Connect your GitHub repo to Vercel
# Automatic deployments on every push to main
```

**Backend (Render):**
```bash
# Create Dockerfile
# Connect to Render web service
# Link to managed PostgreSQL database
```

---

## 🏃‍♂️ Development Workflow

### Team Structure (Hackathon Optimized)

### Team Structure (Hackathon Optimized)

#### **Backend Team** 👩‍💻👨‍💻

**Backend Developer 1: The Architect & API Specialist**
- 🏗️ Flask/FastAPI project structure
- 🗄️ PostgreSQL + TimescaleDB setup
- 🔌 REST API development & CORS configuration
- 🎭 **CRITICAL**: Data simulator for frontend unblocking
- ☁️ Render deployment & integration

**Backend Developer 2: The AI Specialist** 
- 🧠 LSTM glucose prediction model (OhioT1DM dataset)
- 🤖 DQN reinforcement learning agent (simglucose environment)
- 🔬 Model training & optimization
- 📦 Model packaging for API integration

#### **Frontend Team** 👩‍🎨👨‍🎨

**Frontend Developer 1: UI Architect & Data Viz Lead**
- ⚛️ React + Vite project setup
- 🎨 Material-UI component architecture  
- 📊 **STAR FEATURE**: Dual-line glucose chart (Recharts)
- 📱 Responsive design & Vercel deployment

**Frontend Developer 2: State & Features Specialist**
- 🗃️ Zustand state management
- 🔗 Axios API integration
- ✨ Interactive logging modal
- 📸 Camera-based meal logging
- ⚡ Real-time recommendation flow

---

## 📋 API Endpoints

### Core Endpoints
```http
# Authentication
POST /register
POST /login

# Dashboard Data
GET /api/dashboard
→ Complete dashboard data package

# Development (Critical for parallel development)
GET /api/dev/simulate-data  
→ Generates realistic mock data for frontend team

# Glucose Predictions  
GET /api/glucose/prediction
→ LSTM-powered 1-2 hour forecasts

# Smart Dosing
POST /api/dose/recommendation
→ DQN agent recommendations

# Logging
POST /api/log/meal
POST /api/log/image
→ Meal logging with image upload support
```

### Response Examples
```json
// Dashboard Response
{
  "currentGlucose": 120,
  "glucoseHistory": [115, 118, 120],
  "predictions": [125, 128, 130],
  "user": {"name": "John", "target_range": [70, 180]},
  "isLoading": false
}

// Dose Recommendation
{
  "recommendedDose": 4.5,
  "confidence": 0.87,
  "reasoning": "Based on current glucose trend and carb input"
}

// Dev Simulator Response
{
  "message": "Mock data generated successfully",
  "dataPoints": 288,
  "timeRange": "24 hours"
}
```

---

## 🎮 Demo Features & Development Roadmap

### 🌟 **Hackathon Victory Features**

#### **Day 1 Morning: Foundation**
- ✅ **Backend**: Flask API scaffolding + PostgreSQL setup
- ✅ **Frontend**: React + Vite + MUI project structure
- 🎯 **Critical Path**: Data simulator endpoint (`/api/dev/simulate-data`)

#### **Day 1 Afternoon: The Magic**
- 📊 **Star Feature**: Dual-line glucose chart (historical solid, predicted dashed)
- 🧠 **LSTM Model**: Trained on OhioT1DM dataset, packaged for API
- 🤖 **DQN Agent**: Training in simglucose environment
- 🗃️ **State Management**: Zustand store with live data integration

#### **Day 2: Integration & Polish**
- ⚡ **Recommendation Flow**: Carbs input → AI dose suggestion (< 2 seconds)
- 📸 **Smart Logging**: Camera upload → Mock carb estimation
- ☁️ **Deployment**: Live demo on Vercel + Render
- 🎨 **UI Polish**: Responsive design, loading states, error handling

### 🏆 **Judge-Winning Moments**

1. **📈 Predictive Chart**
   ```
   "Watch this - the solid line shows actual glucose,
   the dashed line shows where our AI thinks it's heading.
   This transforms reactive care into proactive management."
   ```

2. **⚡ Lightning-Fast Recommendations**  
   ```
   "I'll enter 45g of carbs... *click* ... and instantly
   our reinforcement learning agent suggests 4.2 units
   based on current glucose trends."
   ```

3. **🌐 Universal Access**
   ```
   "No app store, no installation, no device restrictions.
   Works on any browser, anywhere, instantly accessible
   in medical emergencies."
   ```

4. **🔬 Technical Depth**
   ```
   "Behind the scenes: LSTM neural networks for prediction,
   Deep Q-Networks for dosing, all trained on medical-grade
   simulation environments. This is real AI, not just APIs."
   ```

---

## 🔬 AI Models Deep Dive

### LSTM Glucose Prediction Model
```python
# Architecture for 1-2 hour glucose forecasting
model = Sequential([
    LSTM(50, return_sequences=True, input_shape=(sequence_length, features)),
    LSTM(50, return_sequences=False),
    Dense(25, activation='relu'),
    Dense(prediction_horizon)  # 12 points (1-2 hours at 10min intervals)
])

# Training Data: OhioT1DM dataset
# Input: [glucose_history, insulin_history, carb_history]
# Output: [future_glucose_12_points]
```

### DQN Reinforcement Learning Agent  
```python
# Environment: simglucose diabetes simulator
# State Space: [current_glucose, glucose_trend, time_since_last_meal, active_insulin]
# Action Space: insulin_dose (continuous, 0-20 units)
# Reward Function:
reward = time_in_range_bonus - (hypoglycemia_penalty * 10) - hyperglycemia_penalty

# Training with Stable-Baselines3 DQN
agent = DQN('MlpPolicy', env, learning_rate=1e-3, 
            buffer_size=10000, learning_starts=1000)
```

### Integration Wrapper Functions
```python
def predict_future_glucose(recent_glucose_list):
    """
    Takes: List of recent glucose readings
    Returns: List of predicted glucose values (next 1-2 hours)
    """
    
def get_dose_recommendation(current_glucose, meal_carbs):
    """
    Takes: Current glucose level, planned meal carbs
    Returns: Recommended insulin dose from trained DQN agent
    """
```

---

## 📊 Development Status

### ✅ **Day 1 Morning (Foundation Complete)**
- [x] Project architecture finalized
- [x] Technology stack selected (100% free)
- [x] Team roles and responsibilities defined
- [x] Development roadmap locked in

### 🔄 **Day 1 Afternoon (In Progress)**  
- [ ] Flask API scaffolding (Backend Dev 1) - **90% complete**
- [ ] Data simulator endpoint (Backend Dev 1) - **CRITICAL PRIORITY**
- [ ] React + MUI setup (Frontend Dev 1) - **85% complete**  
- [ ] LSTM model training (Backend Dev 2) - **70% complete**
- [ ] Zustand state management (Frontend Dev 2) - **60% complete**

### 📅 **Day 2 (Final Sprint)**
- [ ] **Star Feature**: Dual-line glucose chart
- [ ] AI model integration into API endpoints
- [ ] Recommendation flow implementation
- [ ] Camera-based logging
- [ ] Production deployment (Vercel + Render)
- [ ] Demo preparation & testing

### 🎯 **Success Metrics**
- ⚡ **< 2 second** response time for dose recommendations
- 📊 **Smooth 60fps** chart animations and interactions  
- 🌐 **Cross-browser** compatibility (Chrome, Firefox, Safari)
- 📱 **Mobile responsive** design (works on phones, tablets, desktop)
- 🧠 **Live AI predictions** with reasonable accuracy on demo data

---

## 🎯 Hackathon Success Metrics

### Technical Excellence
- ✅ Working AI models with real predictions
- ✅ Seamless mobile experience
- ✅ Live data integration
- ✅ Computer vision functionality

### Innovation Impact
- 🎯 Addresses real medical need
- 🎯 Novel application of RL in healthcare
- 🎯 User experience breakthrough
- 🎯 Scalable, production-ready architecture

---

## 🤝 Contributing

We're moving fast! Here's how to jump in:

### Immediate Priorities (Next 8 Hours)
```bash
# CRITICAL PATH - MUST COMPLETE TODAY
1. Backend Dev 1: Data simulator endpoint (/api/dev/simulate-data)
   └── This unblocks the entire frontend team
   
2. Frontend Dev 1: Glucose chart with dual lines (Recharts)
   └── This is your demo centerpiece
   
3. Backend Dev 2: LSTM model training completion
   └── Package predict_future_glucose() function
   
4. Frontend Dev 2: State management + API integration
   └── Connect chart to live backend data

# SECONDARY PRIORITIES  
5. Recommendation flow (carbs → dose suggestion)
6. Camera upload functionality
7. UI polish and responsiveness
8. Deployment pipeline setup
```

### Development Guidelines
- 🎯 **Demo First**: Prioritize features that wow judges
- ⚡ **Speed Over Perfection**: Working > polished for hackathon
- 🔗 **Unblock Early**: Simulator data enables parallel development  
- 📊 **Chart is King**: The glucose visualization is your winning feature
- 🧠 **AI Must Work**: Models should produce reasonable outputs
- 🌐 **Web-First**: Optimize for browser performance, not mobile apps

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**Built with ❤️ by the Aura Team**

- 🏗️ **Backend Architect** - API & Infrastructure
- 🧠 **AI Specialist** - ML Models & Predictions  
- 🎨 **UI/UX Designer** - Beautiful Interfaces
- ⚡ **Integration Master** - Making it all work together

---

## 🔮 Future Vision

Project Aura's web-first approach enables rapid scaling and feature development:

#### **Phase 2: Advanced Intelligence**
- 🧬 **Personalization Engine**: Learn individual insulin sensitivity patterns
- 📱 **Progressive Web App**: Offline functionality, push notifications
- 🔗 **CGM Integration**: Real-time glucose streaming from Dexcom, FreeStyle
- 📊 **Advanced Analytics**: HbA1c predictions, time-in-range optimization

#### **Phase 3: Healthcare Ecosystem**
- 🏥 **Provider Dashboard**: Share insights with endocrinologists
- 👥 **Community Features**: Anonymous benchmarking, peer support
- 🔬 **Research Platform**: Opt-in data contribution for diabetes research
- 🌍 **Global Scale**: Multi-language support, regional medical guidelines

#### **Phase 4: AI Evolution**  
- 🤖 **Multi-Modal Learning**: Combine glucose, activity, sleep, stress data
- 🔮 **Long-term Forecasting**: Weekly/monthly glucose trend predictions
- 💊 **Medication Optimization**: AI-suggested therapy adjustments
- 🧬 **Precision Medicine**: Genetic factors in diabetes managementare
- 🤖 **Advanced AI**: Multi-modal learning, federated learning across users

---

<div align="center">

### 🚀 **Ready to revolutionize diabetes management?**

[Get Started](#-quick-start) • [View Demo](https://demo.projectaura.ai) • [Join the Team](mailto:team@projectaura.ai)

**⭐ Star this repo if you believe in AI-powered healthcare!**

</div>