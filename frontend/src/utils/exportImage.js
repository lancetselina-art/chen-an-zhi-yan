function svgMarkup(svgElement) {
  if (svgElement?.outerHTML) return svgElement.outerHTML
  if (typeof XMLSerializer !== 'undefined') return new XMLSerializer().serializeToString(svgElement)
  throw new Error('当前环境不支持 SVG 导出')
}

export function exportSvgAsPng(svgElement, filename) {
  if (!svgElement) return Promise.reject(new Error('未找到架构图'))
  const width = Number(svgElement.getAttribute?.('width') || svgElement.viewBox?.baseVal?.width || 1200)
  const height = Number(svgElement.getAttribute?.('height') || svgElement.viewBox?.baseVal?.height || 720)
  const svgBlob = new Blob([svgMarkup(svgElement)], { type: 'image/svg+xml;charset=utf-8' })
  const svgUrl = URL.createObjectURL(svgBlob)

  return new Promise((resolve, reject) => {
    const image = document.createElement('img')
    image.onload = () => {
      try {
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        canvas.getContext('2d').drawImage(image, 0, 0, width, height)
        canvas.toBlob((pngBlob) => {
          URL.revokeObjectURL(svgUrl)
          if (!pngBlob) {
            reject(new Error('PNG 图片生成失败'))
            return
          }
          const link = document.createElement('a')
          link.href = URL.createObjectURL(pngBlob)
          link.download = filename
          document.body.append(link)
          link.click()
          document.body.removeChild(link)
          URL.revokeObjectURL(link.href)
          resolve()
        }, 'image/png')
      } catch (error) {
        URL.revokeObjectURL(svgUrl)
        reject(error)
      }
    }
    image.onerror = () => {
      URL.revokeObjectURL(svgUrl)
      reject(new Error('架构图加载失败'))
    }
    image.src = svgUrl
  })
}
