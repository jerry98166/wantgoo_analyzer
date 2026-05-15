<template>
  <div class="stock-detail">
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header" style="display: flex; align-items: center; gap: 20px;">
              <span>個股深度分析 (技術面與成本線)</span>
              <el-input 
                v-model="stockId" 
                placeholder="請輸入股票代號 (如: 2330)" 
                style="width: 200px"
                @keyup.enter="fetchStock"
              >
                <template #append>
                  <el-button icon="Search" @click="fetchStock" />
                </template>
              </el-input>
            </div>
          </template>

          <div v-if="stockData && !loading" style="margin-bottom: 20px; display: flex; gap: 15px; flex-wrap: wrap;">
            <el-tag type="info" effect="dark" size="large">
              MA20 扣抵價: {{ stockData.ma20_deduction[stockData.ma20_deduction.length - 1].toFixed(2) }} 
              <el-tooltip content="扣抵值為20天前的收盤價。若目前股價高於扣抵價，代表未來均線將上揚，形成支撐；反之則下彎，形成壓力。" placement="top">
                <el-icon style="margin-left: 5px; cursor: pointer;"><InfoFilled /></el-icon>
              </el-tooltip>
            </el-tag>
            <el-tag :type="stockData.ma20_trend.includes('上揚') ? 'danger' : 'success'" effect="dark" size="large">
              月線趨勢: {{ stockData.ma20_trend }}
            </el-tag>
          </div>
          
          <div v-loading="loading" style="height: 850px;">
             <v-chart v-if="chartOption" :option="chartOption" autoresize />
             <div v-else-if="!loading" style="text-align:center; padding-top: 100px;">
                無資料或請搜尋股票
             </div>
          </div>

          <!-- 策略回測區域 -->
          <el-divider v-if="stockData">策略模擬回測 (均線趨勢策略)</el-divider>
          <div v-if="stockData" class="backtest-section" style="padding: 20px; background: var(--bg-color); border-radius: 8px;">
            <el-row :gutter="20">
              <el-col :span="8">
                <el-statistic title="策略累積報酬率" :value="backtestResult.totalReturn" suffix="%" :precision="2" :value-style="{ color: backtestResult.totalReturn > 0 ? '#f56c6c' : '#67c23a' }" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="交易次數" :value="backtestResult.tradeCount" />
              </el-col>
              <el-col :span="8">
                <el-statistic title="勝率" :value="backtestResult.winRate" suffix="%" :precision="2" />
              </el-col>
            </el-row>
            <div style="margin-top: 15px; font-size: 13px; color: #909399;">
              * 策略說明：當日收盤價站上 20日均線(MA20) 買入，跌破 MA20 賣出。不計手續費與稅。
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { apiClient } from '../api'

const stockId = ref('2330')
const stockData = ref(null)
const loading = ref(false)

const fetchStock = async () => {
  if (!stockId.value) return
  loading.value = true
  try {
    const { data } = await apiClient.get(`/api/stock/${stockId.value}`)
    if (data.error) {
       stockData.value = null
       alert("找不到該股票代號")
    } else {
       stockData.value = data
    }
  } catch (error) {
    console.error('Failed to fetch stock', error)
  } finally {
    loading.value = false
  }
}

const backtestResult = computed(() => {
  if (!stockData.value) return { totalReturn: 0, tradeCount: 0, winRate: 0 }
  
  const prices = stockData.value.kline_data.map(k => k[1]) // Close prices
  const ma20 = stockData.value.ma20
  
  let position = 0 // 0: cash, 1: stock
  let buyPrice = 0
  let totalProfitPct = 0
  let tradeCount = 0
  let winCount = 0
  
  for (let i = 1; i < prices.length; i++) {
    const prevClose = prices[i-1]
    const currClose = prices[i]
    const currMA = ma20[i]
    
    if (position === 0 && currClose > currMA && currMA > 0) {
      // Buy signal
      position = 1
      buyPrice = currClose
    } else if (position === 1 && currClose < currMA) {
      // Sell signal
      position = 0
      const profit = (currClose - buyPrice) / buyPrice
      totalProfitPct += profit
      tradeCount++
      if (profit > 0) winCount++
    }
  }
  
  // If still holding at the end
  if (position === 1) {
    const lastPrice = prices[prices.length - 1]
    const profit = (lastPrice - buyPrice) / buyPrice
    totalProfitPct += profit
    tradeCount++
    if (profit > 0) winCount++
  }
  
  return {
    totalReturn: totalProfitPct * 100,
    tradeCount: tradeCount,
    winRate: tradeCount > 0 ? (winCount / tradeCount) * 100 : 0
  }
})

onMounted(() => {
  if (window.selectedStockId) {
    stockId.value = window.selectedStockId
    window.selectedStockId = null // clear it
  }
  fetchStock()
})

const chartOption = computed(() => {
  if (!stockData.value) return null
  
  const d = stockData.value

  // 計算分價量表 (Volume Profile)
  let minPrice = Infinity;
  let maxPrice = -Infinity;
  d.kline_data.forEach(item => {
    // kline: [Open, Close, Low, High]
    if (item[2] < minPrice) minPrice = item[2];
    if (item[3] > maxPrice) maxPrice = item[3];
  });
  
  const binCount = 40;
  const binSize = (maxPrice - minPrice) / binCount;
  const vpBins = new Array(binCount).fill(0);
  const vpLabels = new Array(binCount).fill('');
  
  for (let i = 0; i < binCount; i++) {
    vpLabels[i] = (minPrice + i * binSize + binSize/2).toFixed(1);
  }

  d.kline_data.forEach((item, index) => {
    const vol = d.volumes[index];
    const typicalPrice = (item[0] + item[1] + item[2] + item[3]) / 4;
    let binIndex = Math.floor((typicalPrice - minPrice) / binSize);
    if (binIndex >= binCount) binIndex = binCount - 1;
    if (binIndex < 0) binIndex = 0;
    vpBins[binIndex] += vol;
  });
  
  return {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'cross' }
    },
    legend: {
      data: ['K線', 'MA5', 'MA20', '主力成本 (VWAP)', '成交量', 'RSI (14)', 'K (9)', 'D (9)', 'MACD', 'MACD Signal', '分價量表'],
      top: 0
    },
    grid: [
      { left: '8%', right: '22%', top: '5%', height: '35%' },  // K線主圖
      { left: '8%', right: '22%', top: '43%', height: '10%' }, // 成交量
      { left: '8%', right: '22%', top: '56%', height: '10%' }, // RSI
      { left: '8%', right: '22%', top: '69%', height: '10%' }, // KD
      { left: '8%', right: '22%', top: '82%', height: '10%' }, // MACD
      { left: '82%', right: '5%', top: '5%', height: '35%' }   // 分價量表 (右側)
    ],
    xAxis: [
      { type: 'category', data: d.dates, gridIndex: 0, axisLine: { onZero: false } },
      { type: 'category', data: d.dates, gridIndex: 1, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: d.dates, gridIndex: 2, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: d.dates, gridIndex: 3, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'category', data: d.dates, gridIndex: 4, axisLabel: { show: false }, axisTick: { show: false } },
      { type: 'value', gridIndex: 5, axisLabel: { show: false }, splitLine: { show: false } } // 分價量表 X軸 (成交量)
    ],
    yAxis: [
      { type: 'value', gridIndex: 0, scale: true },
      { type: 'value', gridIndex: 1, name: '成交量' },
      { type: 'value', gridIndex: 2, name: 'RSI' },
      { type: 'value', gridIndex: 3, name: 'KD' },
      { type: 'value', gridIndex: 4, name: 'MACD' },
      { type: 'category', gridIndex: 5, data: vpLabels, position: 'right', axisLabel: { fontSize: 10 } } // 分價量表 Y軸 (價格)
    ],
    dataZoom: [
      { type: 'inside', xAxisIndex: [0, 1, 2, 3, 4], start: 30, end: 100 },
      { show: true, type: 'slider', xAxisIndex: [0, 1, 2, 3, 4], bottom: '0%' }
    ],
    series: [
      {
        name: 'K線',
        type: 'candlestick',
        data: d.kline_data,
        itemStyle: {
          color: '#f56c6c',
          color0: '#67c23a',
          borderColor: '#f56c6c',
          borderColor0: '#67c23a'
        },
        markPoint: {
          label: {
            show: true,
            formatter: function (param) {
              return param.name;
            },
            position: 'bottom',
            distance: 10,
            fontSize: 10,
            color: 'var(--el-text-color-primary)',
            backgroundColor: 'rgba(255, 255, 255, 0.7)',
            padding: [2, 4],
            borderRadius: 4
          },
          data: (d.patterns || []).map(p => ({
            name: p.pattern.split(' ')[0], // 只取中文名稱部分
            value: p.pattern,
            xAxis: p.date,
            yAxis: p.price,
            itemStyle: { color: '#e6a23c' },
            symbol: 'pin',
            symbolSize: 10
          }))
        }
      },
      {
        name: 'MA5',
        type: 'line',
        data: d.ma5,
        smooth: true,
        lineStyle: { opacity: 0.5 },
        symbol: 'none'
      },
      {
        name: 'MA20',
        type: 'line',
        data: d.ma20,
        smooth: true,
        lineStyle: { opacity: 0.5 },
        symbol: 'none'
      },
      {
        name: '主力成本 (VWAP)',
        type: 'line',
        data: d.vwap20,
        smooth: true,
        lineStyle: { color: '#9c27b0', width: 2, type: 'dashed' },
        itemStyle: { color: '#9c27b0' },
        symbol: 'none'
      },
      {
        name: '成交量',
        type: 'bar',
        xAxisIndex: 1,
        yAxisIndex: 1,
        data: d.volumes,
        itemStyle: {
          color: function(params) {
            const k = d.kline_data[params.dataIndex]
            return k[1] > k[0] ? '#f56c6c' : '#67c23a'
          }
        }
      },
      {
        name: 'RSI (14)',
        type: 'line',
        xAxisIndex: 2,
        yAxisIndex: 2,
        data: d.rsi,
        lineStyle: { color: '#e6a23c' },
        itemStyle: { color: '#e6a23c' },
        symbol: 'none'
      },
      {
        name: 'K (9)',
        type: 'line',
        xAxisIndex: 3,
        yAxisIndex: 3,
        data: d.k,
        lineStyle: { color: '#409eff', width: 1 },
        itemStyle: { color: '#409eff' },
        symbol: 'none'
      },
      {
        name: 'D (9)',
        type: 'line',
        xAxisIndex: 3,
        yAxisIndex: 3,
        data: d.d,
        lineStyle: { color: '#e6a23c', width: 1 },
        itemStyle: { color: '#e6a23c' },
        symbol: 'none'
      },
      {
        name: 'MACD Hist',
        type: 'bar',
        xAxisIndex: 4,
        yAxisIndex: 4,
        data: d.macd_hist,
        itemStyle: {
          color: function(params) {
            return params.value > 0 ? '#f56c6c' : '#67c23a'
          }
        }
      },
      {
        name: 'MACD',
        type: 'line',
        xAxisIndex: 4,
        yAxisIndex: 4,
        data: d.macd,
        lineStyle: { color: '#409eff', width: 1 },
        itemStyle: { color: '#409eff' },
        symbol: 'none'
      },
      {
        name: 'MACD Signal',
        type: 'line',
        xAxisIndex: 4,
        yAxisIndex: 4,
        data: d.macd_signal,
        lineStyle: { color: '#e6a23c', width: 1 },
        itemStyle: { color: '#e6a23c' },
        symbol: 'none'
      },
      {
        name: '分價量表',
        type: 'bar',
        xAxisIndex: 5,
        yAxisIndex: 5,
        data: vpBins,
        itemStyle: { color: '#b3e19d', opacity: 0.6 },
        tooltip: {
          formatter: function(params) {
            return `價格區間: ${params.name}<br/>累積成交量: ${params.value}`;
          }
        }
      }
    ]
  }
})

</script>

<style scoped>
.card-header {
  font-weight: bold;
}
</style>