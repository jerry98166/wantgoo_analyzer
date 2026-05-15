<template>
  <el-container class="layout-container">
    
    <!-- 側邊欄 -->
    <el-aside width="260px" class="aside">
      <div class="logo">
        <el-icon :size="28" color="#409EFC"><DataAnalysis /></el-icon>
        <span>台股籌碼大數據</span>
      </div>
      
      <el-menu 
        :default-active="activeMenu" 
        @select="handleSelect" 
        class="el-menu-vertical"
        background-color="#1d1e23"
        text-color="#a6adb4"
        active-text-color="#ffffff"
      >
        <div class="menu-category" style="margin-top: 15px;">核心功能</div>
        <el-menu-item index="MarketSummary">
          <el-icon><Odometer /></el-icon>
          <span>大盤與輿情總覽</span>
        </el-menu-item>
        <el-menu-item index="StockHeatmap">
          <el-icon><Grid /></el-icon>
          <span>股票熱力圖</span>
        </el-menu-item>
        <el-menu-item index="Watchlist">
          <el-icon><Star /></el-icon>
          <span>自選股與警示</span>
        </el-menu-item>
        <el-menu-item index="SmartMoney">
          <el-icon><Magnet /></el-icon>
          <span>主力籌碼深度追蹤</span>
        </el-menu-item>
        <el-menu-item index="Screener">
          <el-icon><Filter /></el-icon>
          <span>多條件智慧選股</span>
        </el-menu-item>
        <el-menu-item index="InvestorDashboard">
          <el-icon><DataBoard /></el-icon>
          <span>投資決策儀表板</span>
        </el-menu-item>
        <el-menu-item index="MarketBreadth">
          <el-icon><PieChart /></el-icon>
          <span>大盤結構與產業資金</span>
        </el-menu-item>
        <el-menu-item index="InstitutionalTracking">
          <el-icon><Aim /></el-icon>
          <span>法人資金追蹤</span>
        </el-menu-item>
        <el-menu-item index="RetailAndLeaders">
          <el-icon><UserFilled /></el-icon>
          <span>散戶動向與人氣榜</span>
        </el-menu-item>
        <el-menu-item index="StockDetail">
          <el-icon><TrendCharts /></el-icon>
          <span>個股技術與籌碼分析</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    
    <!-- 右側內容區塊 -->
    <el-container>
      <el-header class="header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item>首頁</el-breadcrumb-item>
            <el-breadcrumb-item>{{ currentTitle }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right" style="display: flex; align-items: center; gap: 15px;">
          <el-switch
            v-model="isDark"
            inline-prompt
            active-icon="Moon"
            inactive-icon="Sunny"
            style="--el-switch-on-color: #2C2C2C; --el-switch-off-color: #f2f2f2;"
          />
        </div>
      </el-header>
      
      <el-main class="main-content">
        <transition name="fade-transform" mode="out-in">
          <component :is="currentComponent" />
        </transition>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, watch } from 'vue'

import MarketSummary from './components/MarketSummary.vue'
import Watchlist from './components/Watchlist.vue'
import SmartMoney from './components/SmartMoney.vue'
import Screener from './components/Screener.vue'
import InvestorDashboard from './components/InvestorDashboard.vue'
import MarketBreadth from './components/MarketBreadth.vue'
import InstitutionalTracking from './components/InstitutionalTracking.vue'
import RetailAndLeaders from './components/RetailAndLeaders.vue'
import StockDetail from './components/StockDetail.vue'
import StockHeatmap from './components/StockHeatmap.vue'
import { onMounted, onUnmounted } from 'vue'

const activeMenu = ref('MarketSummary')
const isDark = ref(false)

watch(isDark, (val) => {
  if (val) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
})

const handleViewStock = (e) => {
  activeMenu.value = 'StockDetail'
  window.selectedStockId = e.detail
}

onMounted(() => {
  window.addEventListener('view-stock', handleViewStock)
})

onUnmounted(() => {
  window.removeEventListener('view-stock', handleViewStock)
})

const componentsMap = {
  MarketSummary: { comp: MarketSummary, title: '大盤與輿情總覽' },
  StockHeatmap: { comp: StockHeatmap, title: '股票熱力圖' },
  Watchlist: { comp: Watchlist, title: '自選股與警示' },
  SmartMoney: { comp: SmartMoney, title: '主力籌碼深度追蹤' },
  Screener: { comp: Screener, title: '多條件智慧選股' },
  InvestorDashboard: { comp: InvestorDashboard, title: '投資決策儀表板' },
  MarketBreadth: { comp: MarketBreadth, title: '大盤結構與產業資金' },
  InstitutionalTracking: { comp: InstitutionalTracking, title: '法人資金追蹤' },
  RetailAndLeaders: { comp: RetailAndLeaders, title: '散戶動向與人氣榜' },
  StockDetail: { comp: StockDetail, title: '個股技術與籌碼分析' }
}

const currentComponent = computed(() => componentsMap[activeMenu.value].comp)
const currentTitle = computed(() => componentsMap[activeMenu.value].title)

const handleSelect = (index) => {
  activeMenu.value = index
}
</script>

<style scoped>
.layout-container {
  height: 100vh;
}
.aside {
  background-color: var(--sidebar-bg);
  box-shadow: 2px 0 8px 0 rgba(29, 30, 35, 0.5);
  z-index: 10;
  display: flex;
  flex-direction: column;
}
.logo {
  height: 70px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  font-size: 20px;
  font-weight: bold;
  color: #ffffff;
  background-color: #151619;
}
.menu-category {
  padding: 10px 20px 5px;
  font-size: 12px;
  color: #606266;
  text-transform: uppercase;
  letter-spacing: 1px;
}
.el-menu-vertical {
  border-right: none;
  flex: 1;
  overflow-y: auto;
}
.el-menu-item.is-active {
  background-color: var(--sidebar-active-bg) !important;
  border-radius: 0 25px 25px 0;
  margin-right: 15px;
}
.header {
  background-color: var(--card-bg);
  border-bottom: 1px solid var(--border-color);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 30px;
  height: 60px;
  transition: background-color 0.3s, border-color 0.3s;
}
.main-content {
  background-color: var(--bg-color);
  padding: 30px 40px;
  overflow-y: auto;
}

.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1);
}
.fade-transform-enter-from {
  opacity: 0;
  transform: translateY(20px);
}
.fade-transform-leave-to {
  opacity: 0;
  transform: translateY(-20px);
}
</style>
