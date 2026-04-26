<template>
  <div class="empty-state">
    <div class="empty-visual">
      <div class="orbit-ring ring-1">
        <div class="orbit-dot"></div>
      </div>
      <div class="orbit-ring ring-2">
        <div class="orbit-dot"></div>
      </div>
      <div class="orbit-ring ring-3">
        <div class="orbit-dot"></div>
      </div>
      <div class="center-icon">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none">
          <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="url(#emptyGrad)" opacity="0.8"/>
          <path d="M2 17L12 22L22 17" stroke="url(#emptyGrad)" stroke-width="1.5" stroke-linecap="round" fill="none"/>
          <path d="M2 12L12 17L22 12" stroke="url(#emptyGrad)" stroke-width="1.5" stroke-linecap="round" fill="none"/>
          <defs>
            <linearGradient id="emptyGrad" x1="2" y1="2" x2="22" y2="22">
              <stop offset="0%" stop-color="#818cf8"/>
              <stop offset="100%" stop-color="#6366f1"/>
            </linearGradient>
          </defs>
        </svg>
      </div>
    </div>
    <h2 class="empty-title">Welcome to Zenith</h2>
    <p class="empty-desc">Your personal knowledge graph, designed for clarity.<br/>Create a note to begin mapping your thoughts.</p>
    <button class="btn btn-primary empty-cta" @click="$emit('new-note')" id="empty-state-new-note">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 5V19M5 12H19"/>
      </svg>
      Create Your First Note
    </button>
    <div class="empty-shortcuts">
      <div class="shortcut-item">
        <kbd>[[</kbd> <span>Link notes together</span>
      </div>
      <div class="shortcut-item">
        <kbd>![[</kbd> <span>Embed attachments</span>
      </div>
      <div class="shortcut-item">
        <kbd>Drop</kbd> <span>Drag images into editor</span>
      </div>
    </div>
  </div>
</template>

<script setup>
defineEmits(['new-note'])
</script>

<style scoped>
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  padding: var(--space-3xl);
  background:
    radial-gradient(ellipse at 50% 30%, rgba(99, 102, 241, 0.05) 0%, transparent 60%),
    var(--bg-root);
}

/* Animated orbital visual */
.empty-visual {
  position: relative;
  width: 160px;
  height: 160px;
  margin-bottom: var(--space-2xl);
}

.center-icon {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 2;
}

.orbit-ring {
  position: absolute;
  top: 50%;
  left: 50%;
  border-radius: 50%;
  border: 1px solid rgba(99, 102, 241, 0.12);
}

.ring-1 {
  width: 80px; height: 80px;
  margin: -40px 0 0 -40px;
  animation: spin 8s linear infinite;
}
.ring-2 {
  width: 120px; height: 120px;
  margin: -60px 0 0 -60px;
  animation: spin 14s linear infinite reverse;
}
.ring-3 {
  width: 160px; height: 160px;
  margin: -80px 0 0 -80px;
  animation: spin 20s linear infinite;
}

.orbit-dot {
  position: absolute;
  width: 6px;
  height: 6px;
  background: var(--accent-primary);
  border-radius: 50%;
  top: -3px;
  left: 50%;
  margin-left: -3px;
  box-shadow: 0 0 8px rgba(99, 102, 241, 0.5);
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.empty-title {
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: var(--space-sm);
  background: linear-gradient(135deg, var(--text-primary), var(--accent-secondary));
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.empty-desc {
  color: var(--text-tertiary);
  font-size: 0.9rem;
  line-height: 1.6;
  margin-bottom: var(--space-xl);
  max-width: 400px;
}

.empty-cta {
  padding: var(--space-md) var(--space-2xl);
  font-size: 0.9rem;
  margin-bottom: var(--space-3xl);
}

.empty-shortcuts {
  display: flex;
  gap: var(--space-2xl);
}
.shortcut-item {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  font-size: 0.75rem;
  color: var(--text-tertiary);
}
.shortcut-item kbd {
  font-family: var(--font-mono);
  font-size: 0.7rem;
  padding: 2px 8px;
  background: var(--bg-tertiary);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-sm);
  color: var(--accent-secondary);
}
</style>
