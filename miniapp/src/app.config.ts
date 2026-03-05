export default defineAppConfig({
  pages: ['pages/home/index', 'pages/coach/index', 'pages/history/index', 'pages/analysis/index', 'pages/chat/index', 'pages/morning-report/index', 'pages/evening-review/index', 'pages/weekly-summary/index', 'pages/injury-log/index', 'pages/profile/index'],
  tabBar: {
    list: [
      {
        pagePath: 'pages/home/index',
        text: '首页',
      },
      {
        pagePath: 'pages/coach/index',
        text: '教练',
      },
      {
        pagePath: 'pages/history/index',
        text: '历史',
      },
    ],
  },
  window: {
    navigationBarTitleText: 'PaceMind',
  },
})
