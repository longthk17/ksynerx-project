export async function request(service, endpoint, { params, ...options } = {}) {
  const query = new URLSearchParams(Object.entries(params || {}).filter(([, value]) => value !== '' && value != null));
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 60000);
  try {
    const result = await fetch(`/${service}-api/${endpoint}${query.size ? `?${query}` : ''}`, { ...options, signal: controller.signal });
    const raw = await result.text();
    let body;
    try { body = raw ? JSON.parse(raw) : null; } catch { throw new Error(`Service trả về phản hồi không hợp lệ (HTTP ${result.status}).`); }
    if (!result.ok) {
      const detail = body?.errors ?? body?.detail ?? body;
      throw new Error([body?.errorMessage || `Yêu cầu thất bại (HTTP ${result.status})`, detail ? JSON.stringify(detail, null, 2) : ''].join('\n'));
    }
    return body;
  } catch (error) {
    if (error.name === 'AbortError') throw new Error('Service phản hồi quá thời gian chờ. Hãy kiểm tra lại trước khi gửi yêu cầu lần nữa.');
    if (error instanceof TypeError) throw new Error('Không kết nối được service. Kiểm tra backend và cấu hình proxy.');
    throw error;
  } finally { clearTimeout(timer); }
}
