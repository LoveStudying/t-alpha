<template>
  <div class="page">
    <div class="page-header">
      <div>
        <h1 class="page-title">远期规划</h1>
        <p class="page-subtitle">记录 t-alpha 从接口辅助工具走向研究工作台的方向。</p>
      </div>
    </div>

    <section class="surface section-pad roadmap">
      <div v-for="item in items" :key="item.title" class="roadmap-item">
        <el-tag effect="light">{{ item.phase }}</el-tag>
        <h3>{{ item.title }}</h3>
        <p>{{ item.body }}</p>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
const items = [
  {
    phase: 'Data',
    title: '更多数据源和实时快照',
    body: '在 AmazingData 历史 K 线基础上扩展实时快照、基金扩展信息和更多市场状态，用统一页面呈现数据质量。',
  },
  {
    phase: 'Strategy',
    title: '多策略与参数组合',
    body: '把低吸型 T0 扩展为多策略框架，支持参数版本、策略对比、准入解释和报告沉淀。',
  },
  {
    phase: 'Risk',
    title: '更严格的风险过滤',
    body: '增加 ST、流动性、异常波动、财务风险和市场状态过滤，让提醒更像研究候选而不是简单信号。',
  },
  {
    phase: 'Ops',
    title: '任务编排与报告中心',
    body: '把定时任务、提醒发送、失败重试和回测报告集中管理，减少人工查日志和手动调用接口。',
  },
  {
    phase: 'Security',
    title: '权限与部署安全',
    body: '当系统从本地使用走向多人或公网访问，再引入角色权限、审计、限流、HTTPS 和更严格 token 策略。',
  },
  {
    phase: 'Trading',
    title: '只读账户校验优先',
    body: '未来如接入真实账户，优先做只读持仓和资金校验；自动交易不是近期默认方向，需要单独风控和确认机制。',
  },
]
</script>

<style scoped>
.roadmap {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 14px;
}

.roadmap-item {
  padding: 18px;
  border: 1px solid var(--ta-border);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.74);
}

.roadmap-item h3 {
  margin: 12px 0 8px;
}

.roadmap-item p {
  margin: 0;
  color: var(--ta-muted);
  line-height: 1.8;
}
</style>
