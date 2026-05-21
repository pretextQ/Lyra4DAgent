<template>
  <div class="app">
    <header class="header">
      <router-link to="/" class="logo">
        <span class="logo-text">Lyra<span class="logo-accent">4D</span></span>
      </router-link>
      <nav class="nav">
        <router-link to="/" class="nav-link" :class="{ active: $route.path === '/' }">
          优化
        </router-link>
        <router-link to="/history" class="nav-link" :class="{ active: $route.path === '/history' }">
          历史
        </router-link>
      </nav>
    </header>

    <main class="main">
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 32px;
  height: 52px;
  border-bottom: 1px solid var(--border);
  background: var(--bg-page);
  flex-shrink: 0;
}

.logo {
  text-decoration: none;
  color: var(--text-primary);
}

.logo-text {
  font-family: var(--font-mono);
  font-size: 18px;
  font-weight: 500;
  letter-spacing: 0.5px;
}

.logo-accent {
  color: var(--accent);
}

.nav {
  display: flex;
  gap: 4px;
}

.nav-link {
  padding: 6px 14px;
  border-radius: var(--radius);
  text-decoration: none;
  color: var(--text-secondary);
  font-size: 13px;
  font-family: var(--font-ui);
  transition: color 0.15s, background-color 0.15s;
}

.nav-link:hover {
  color: var(--text-primary);
  background: var(--bg-surface);
}

.nav-link.active {
  color: var(--accent);
  background: var(--bg-surface);
}

.main {
  flex: 1;
  display: flex;
  flex-direction: column;
}
</style>
