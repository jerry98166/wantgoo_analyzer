<template>
  <el-container class="layout-container">
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
        <el-menu-item index="DashboardOverview">
          <el-icon><DataBoard /></el-icon>
          <span>戰情室儀表板</span>
        </el-menu-item>
        
        <div class="menu-category" style="margin-top: 15px;">全市場分析</div>
        <el-menu-item index="MarketBreadth">
          <el-icon><Odometer /></el-icon>
          <span>大盤多空結構</span>
        </el-menu-item>
        <el-menu-item index="IndustryAnalysis">
          <el-icon><PieChart /></el-icon>
          <span>產業板塊輪動</span>
        </el-menu-item>
        <el-menu-item index="InstitutionalSynchrony">
          <el-icon><Switch /></el-icon>
          <span>土洋同步與對作</span>
        </el-menu-item>
        <el-menu-item index="InstitutionalRadar">
          <el-icon><Aim /></el-icon>
          <span>特定法人雷達 (投信/自營)</span>
        </el-menu-item>
        <el-menu-item index="RetailSentiment">
          <el-icon><UserFilled /></el-icon>
          <span>散戶 vs 法人對作</span>
        </el-menu-item>

        <div class="menu-category" style="margin-top: 15px;">資金排行</div>
        <el-menu-item index="TurnoverLeaders">
          <el-icon><Coin /></el-icon>
          <span>吸金排行榜 (成交值)</span>
        </el-menu-item>
        <el-menu-item index="CapitalFocus">
          <el-icon><Money /></el-icon>
          <span>法人買超焦點</span>
        </el-menu-item>
        <el-menu-item index="VolumeLeaders">
          <el-icon><DataLine /></el-icon>
          <span>成交重心人氣王</span>
        </el-menu-item>
        <el-menu-item index="ParticipationRank">
          <el-icon><Histogram /></el-icon>
          <span>法人高參與度排行</span>
        </el-menu-item>

        <div class="menu-category" style="margin-top: 15px;">深度探討</div>
        <el-menu-item index="DayTradingRadar">
          <el-icon><Lightning /></el-icon>
          <span>當沖與短線熱點</span>
        </el-menu-item>
        <el-menu-item index="StockScreener">
          <el-icon><Filter /></el-icon>
          <span>AI 多條件選股器</span>
        </el-menu-item>
        <el-menu-item index="SmartMoney">
          <el-icon><Bicycle /></el-icon>
          <span>聰明錢偷偷吃貨</span>
        </el-menu-item>
        <el-menu-item index="Correlation">
          <el-icon><TrendCharts /></el-icon>
          <span>籌碼與股價關聯</span>
        </el-menu-item>
        <el-menu-item index="StockObserver">
          <el-icon><Search /></el-icon>
          <span>個股籌碼指標 (全位)</span>
        </el-menu-item>
        <el-menu-item index="MarketNews">
          <el-icon><Document /></el-icon>
          <span>玩股網市場情緒</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
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
          <el-tag type="info" effect="dark" round v-if="metaDate">
            <el-icon style="vertical-align: middle; margin-right: 4px"><Calendar /></el-icon>
            資料日期：{{ metaDate }}
          </el-tag>
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
import { ref, computed, onMounted } from 'vue'
import axios from 'axios'
import MarketBreadth from './components/MarketBreadth.vue'
import CapitalFocus from './components/CapitalFocus.vue'
import IndustryAnalysis from './components/IndustryAnalysis.vue'
import InstitutionalSynchrony from './components/InstitutionalSynchrony.vue'
import Correlation from './components/Correlation.vue'
import StockObserver from './components/StockObserver.vue'
import MarketNews from './components/MarketNews.vue'
import VolumeLeaders from './components/VolumeLeaders.vue'
import ParticipationRank from './components/ParticipationRank.vue'
import SmartMoney from './components/SmartMoney.vue'
import TurnoverLeaders from './components/TurnoverLeaders.vue'
import StockScreener from './components/StockScreener.vue'
import InstitutionalRadar from './components/InstitutionalRadar.vue'
import DashboardOverview from './components/DashboardOverview.vue'
import DayTradingRadar from './components/DayTradingRadar.vue'
import RetailSentiment from './components/RetailSentiment.vue'
import { watch } from 'vue'

const activeMenu = ref('DashboardOverview')
const metaDate = ref('')
const isDark = ref(false)

watch(isDark, (val) => {
  if (val) {
    document.documentElement.classList.add('dark')
  } else {
    document.documentElement.classList.remove('dark')
  }
})

const componentsMap = {
  DashboardOverview: { comp: DashboardOverview, title: '戰情室儀表板' },
  MarketBreadth: { comp: MarketBreadth, title: '大盤多空結構' },
  TurnoverLeaders: { comp: TurnoverLeaders, title: '吸金排行榜 (成交值)' },
  CapitalFocus: { comp: CapitalFocus, title: '法人買超焦點' },
  IndustryAnalysis: { comp: IndustryAnalysis, title: '產業板塊輪動' },
  InstitutionalSynchrony: { comp: InstitutionalSynchrony, title: '土洋同步與對作' },
  InstitutionalRadar: { comp: InstitutionalRadar, title: '特定法人雷達' },
  RetailSentiment: { comp: RetailSentiment, title: '散戶 vs 法人對作' },
  DayTradingRadar: { comp: DayTradingRadar, title: '當沖與短線熱點' },
  StockScreener: { comp: StockScreener, title: 'AI 多條件選股器' },
  SmartMoney: { comp: SmartMoney, title: '聰明錢偷偷吃貨' },
  Correlation: { comp: Correlation, title: '籌碼與股價關聯' },
  StockObserver: { comp: StockObserver, title: '個股籌碼指標 (全方位)' },
  MarketNews: { comp: MarketNews, title: '玩股網市場情緒' },
  VolumeLeaders: { comp: VolumeLeaders, title: '成交重心人氣王' },
  ParticipationRank: { comp: ParticipationRank, title: '法人高參與度排行' }
}

const currentComponent = computed(() => componentsMap[activeMenu.value].comp)
const currentTitle = computed(() => componentsMap[activeMenu.value].title)

const handleSelect = (index) => {
  activeMenu.value = index
}

const fetchMeta = async () => {
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/meta')
    metaDate.value = data.date
  } catch (error) {
    console.error("Failed to fetch meta:", error)
  }
}

onMounted(() => {
  fetchMeta()
})
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

/* Transitions */
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
