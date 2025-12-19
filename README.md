# 🐾 Jump! Jelly: AI 自動化測試 Agent

![Project Status](https://img.shields.io/badge/Status-Completed-success) ![Score](https://img.shields.io/badge/High_Score-94-gold)

這是我為國立虎尾科技大學進修部入學準備的前導專案。透過 Python (Pygame) 開發，並實作即時物理運算的 AI Agent，達成 94 分的高難度紀錄。

## 📺 AI 實測演示 (Demo)

> **左側**：遊戲實際畫面 (Hell 模式殘影開啟)
> **右側**：AI Agent 即時運算的決策數據 (距離偵測與落地預判)

![AI Agent Demo GIF](你的GIF圖檔連結.gif)
*(建議：這裡放你錄好的 GIF，檔名若是 demo.gif 且放在同目錄，語法就是 `![Demo](demo.gif)`)*

## 🛠️ 核心功能
* **物理預判系統**：不依賴簡單的距離判斷，而是計算拋物線軌跡 $T_{land} = \frac{d_{ground}}{v_{y}}$。
* **視覺回饋**：實作粒子系統 (Particles) 與動態殘影 (Motion Trails)。
* **自動化測試**：一鍵啟動 Agent，自動驗證遊戲關卡的碰撞邏輯。

## 🚀 如何執行
```bash
# 1. 安裝 Pygame
pip install pygame

# 2. 啟動測試
python main.py
