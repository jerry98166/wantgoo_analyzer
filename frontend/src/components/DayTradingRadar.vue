<template>
  <div>
    <h2>當沖與短線熱點 (Day Trading Radar)</h2>
    <p>短線當沖客最需要的是「波動」。本頁面專門掃描當日「高振幅（上衝下洗大）」與「跳空強勢」的熱門股，並過濾掉成交量過低的殭屍股，找出市場最具活力的資金戰場。</p>
    
    <el-row :gutter="20" v-loading="loading">
      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #409EFF; font-weight: bold;">🎢 沖浪客最愛：高振幅排行 (Top 20)</span>
              <br><span style="font-size: 12px; color: #909399;">振幅 = (最高價 - 最低價) / 昨收</span>
            </div>
          </template>
          <el-table :data="highAmplitude" style="width: 100%" height="500">
            <el-table-column prop="Stock_Name" label="名稱" width="100">
              <template #default="scope">
                <strong>{{ scope.row.Stock_Name }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="Amplitude" label="振幅(%)" width="110">
              <template #default="scope">
                <span style="color: #409EFF; font-weight: bold;">
                  {{ scope.row.Amplitude.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="漲跌幅" width="80">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : (scope.row.Change_Pct < 0 ? '#67c23a' : '#909399') }">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Volume" label="成交量(張)">
              <template #default="scope">
                {{ Math.round(scope.row.Volume) }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :span="12">
        <el-card shadow="hover">
          <template #header>
            <div class="card-header">
              <span style="color: #f56c6c; font-weight: bold;">🚀 跳空強勢股 (Top 20)</span>
              <br><span style="font-size: 12px; color: #909399;">開盤即強勢，強者恆強特徵</span>
            </div>
          </template>
          <el-table :data="gapUp" style="width: 100%" height="500">
            <el-table-column prop="Stock_Name" label="名稱" width="100">
              <template #default="scope">
                <strong>{{ scope.row.Stock_Name }}</strong>
              </template>
            </el-table-column>
            <el-table-column prop="Gap_Pct" label="跳空(%)" width="110">
              <template #default="scope">
                <span style="color: #f56c6c; font-weight: bold;">
                  +{{ scope.row.Gap_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column prop="Change_Pct" label="收盤漲幅" width="80">
              <template #default="scope">
                <span :style="{ color: scope.row.Change_Pct > 0 ? '#f56c6c' : (scope.row.Change_Pct < 0 ? '#67c23a' : '#909399') }">
                  {{ scope.row.Change_Pct > 0 ? '+' : '' }}{{ scope.row.Change_Pct.toFixed(2) }}%
                </span>
              </template>
            </el-table-column>
            <el-table-column label="開高走低?">
              <template #default="scope">
                <el-tag :type="scope.row.Change_Pct < scope.row.Gap_Pct ? 'warning' : 'success'">
                  {{ scope.row.Change_Pct < scope.row.Gap_Pct ? '是 (黑K)' : '否 (紅K)' }}
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const highAmplitude = ref([])
const gapUp = ref([])

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/day-trading')
    highAmplitude.value = data.high_amplitude
    gapUp.value = data.gap_up
  } catch (e) {
    console.error(e)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchData()
})
</script>
