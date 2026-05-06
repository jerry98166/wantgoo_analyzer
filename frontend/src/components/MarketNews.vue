<template>
  <div>
    <h2>玩股網市場情緒與熱點追蹤</h2>
    <p>透過網路爬蟲即時擷取玩股網 (WantGoo) 上的熱門財經文章與專欄，快速掌握散戶與市場大師關注的最新焦點話題。</p>
    
    <div v-loading="loading">
      <el-row :gutter="20" v-if="articles.length > 0">
        <el-col :span="8" v-for="(article, index) in articles" :key="index" style="margin-bottom: 20px;">
          <el-card shadow="hover" class="news-card">
            <div class="news-icon">
              <el-icon :size="32" color="#409EFF"><Reading /></el-icon>
            </div>
            <div class="news-content">
              <h3 class="news-title">
                <a :href="article.link" target="_blank">{{ article.title }}</a>
              </h3>
              <div class="news-meta">
                <el-tag size="small" type="info" effect="plain">玩股網熱門</el-tag>
                <el-button type="primary" link :icon="'Link'" @click="openLink(article.link)">閱讀全文</el-button>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
      <el-empty v-else description="目前無法取得文章列表，請稍後再試。" />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import axios from 'axios'

const loading = ref(false)
const articles = ref([])

const openLink = (url) => {
  window.open(url, '_blank')
}

const fetchData = async () => {
  loading.value = true
  try {
    const { data } = await axios.get('http://127.0.0.1:8000/api/articles')
    articles.value = data
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

<style scoped>
.news-card {
  height: 100%;
  display: flex;
  flex-direction: column;
  transition: transform 0.2s ease;
}
.news-card:hover {
  transform: translateY(-5px);
}
.news-icon {
  text-align: center;
  margin-bottom: 15px;
  background: #f0f8ff;
  padding: 15px;
  border-radius: 50%;
  width: 32px;
  height: 32px;
  margin: 0 auto 15px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.news-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
.news-title {
  font-size: 16px;
  line-height: 1.5;
  margin-top: 0;
  margin-bottom: 20px;
}
.news-title a {
  color: #303133;
  text-decoration: none;
}
.news-title a:hover {
  color: #409EFF;
}
.news-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid #ebeef5;
  padding-top: 15px;
}
</style>
