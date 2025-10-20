import { ref, onMounted, onUnmounted } from 'vue'

/**
 * Composable for responsive design breakpoints
 * Provides reactive breakpoint detection for mobile, tablet, and desktop
 */
export function useResponsive() {
  const isMobile = ref(false)
  const isTablet = ref(false)
  const isDesktop = ref(false)
  const screenWidth = ref(0)

  // Breakpoints
  const MOBILE_MAX = 767
  const TABLET_MIN = 768
  const TABLET_MAX = 1023
  const DESKTOP_MIN = 1024

  const updateBreakpoint = () => {
    const width = window.innerWidth
    screenWidth.value = width
    
    isMobile.value = width <= MOBILE_MAX
    isTablet.value = width >= TABLET_MIN && width <= TABLET_MAX
    isDesktop.value = width >= DESKTOP_MIN
  }

  onMounted(() => {
    updateBreakpoint()
    window.addEventListener('resize', updateBreakpoint)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', updateBreakpoint)
  })

  return {
    isMobile,
    isTablet,
    isDesktop,
    screenWidth,
    // Utility getters
    isMobileOrTablet: () => isMobile.value || isTablet.value,
    isTabletOrDesktop: () => isTablet.value || isDesktop.value
  }
}
