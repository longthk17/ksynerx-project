import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { request } from './api';
import './styles.css';

function Notice({ error, success }) {
  return <>{error && <div className="notice error" role="alert">{error}</div>}{success && <div className="notice success" role="status">{success}</div>}</>;
}

function ProductTable({ products, loading }) {
  const [selected, setSelected] = useState(null);
  return <><div className="table-wrap"><table><thead><tr><th>SKU</th><th>Sản phẩm</th><th>SKU đối tác</th><th>Đơn vị</th><th>Hạn sử dụng</th><th>Chi tiết</th></tr></thead><tbody>
    {loading ? <tr><td colSpan="6" className="empty">Đang tải dữ liệu…</td></tr> : products.length ? products.map((p, index) => <tr key={p.id ?? `${p.sku}-${index}`}><td><code>{p.sku}</code></td><td><strong>{p.productName}</strong><small>{p.categories?.map(c => c.categoryName).join(', ') || 'Chưa có danh mục'}</small></td><td>{p.partnerSKU || '—'}</td><td>{p.unitName} <small>{p.unitCode}</small></td><td><span className="tag">{p.isExpiryDate ? 'Có theo dõi' : 'Không'}</span></td><td><button className="text-button" onClick={() => setSelected(p)}>Xem</button></td></tr>) : <tr><td colSpan="6" className="empty">Không có sản phẩm để hiển thị.</td></tr>}
  </tbody></table></div>{selected && <div className="modal-backdrop" onClick={() => setSelected(null)}><section className="modal" role="dialog" aria-modal="true" aria-label="Chi tiết sản phẩm" onClick={e => e.stopPropagation()}><div className="section-head"><h2>{selected.productName}</h2><button autoFocus onClick={() => setSelected(null)}>Đóng</button></div><pre>{JSON.stringify(selected, null, 2)}</pre></section></div>}</>;
}

const initialProduct = { sku: '', partnerSKU: '', productName: '', unitCode: '', unitName: '', serialType: 0, isExpiryDate: false };
function Inventory() {
  const [products, setProducts] = useState([]);
  const [pagination, setPagination] = useState(null);
  const [filters, setFilters] = useState({ Keyword: '', SKUs: '', PartnerSKUs: '', PageSize: 10 });
  const [applied, setApplied] = useState(filters);
  const [page, setPage] = useState(0);
  const [revision, setRevision] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [creating, setCreating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [product, setProduct] = useState(initialProduct);
  const [categories, setCategories] = useState('[]');
  const [units, setUnits] = useState('[]');
  useEffect(() => {
    let active = true;
    setLoading(true); setError(''); setProducts([]); setPagination(null);
    request('inventory', 'product', { params: { ...applied, PageIndex: page } }).then(data => {
      if (active) { setProducts(data.results); setPagination(data); }
    }).catch(err => { if (active) setError(err.message); }).finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [applied, page, revision]);
  async function createProduct(event) {
    event.preventDefault(); setSaving(true); setError(''); setSuccess('');
    try {
      const parsedCategories = JSON.parse(categories), parsedUnits = JSON.parse(units);
      if (!Array.isArray(parsedCategories) || !Array.isArray(parsedUnits)) throw new Error('Danh mục và đơn vị quy đổi phải là mảng JSON.');
      await request('inventory', 'product', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify([{ ...product, partnerSKU: product.partnerSKU || null, serialType: Number(product.serialType), categories: parsedCategories, productUnits: parsedUnits }]) });
      setSuccess(`Đã tạo sản phẩm ${product.sku}.`); setCreating(false); setProduct(initialProduct); setCategories('[]'); setUnits('[]'); setRevision(r => r + 1);
    } catch (err) { setError(err.message); } finally { setSaving(false); }
  }
  return <><div className="section-head"><div><p className="eyebrow">INVENTORY SERVICE</p><h1>Danh sách sản phẩm</h1><p>Quản lý dữ liệu sản phẩm tại một nơi.</p></div><button className="primary" onClick={() => setCreating(v => !v)}>{creating ? 'Đóng biểu mẫu' : '+ Tạo sản phẩm'}</button></div>
    <Notice error={error} success={success}/>
    {creating && <form className="panel" onSubmit={createProduct}><h2>Sản phẩm mới</h2><fieldset disabled={saving}><div className="form-grid">{[['sku', 'SKU', 100], ['productName', 'Tên sản phẩm', 255], ['partnerSKU', 'SKU đối tác', 100], ['unitCode', 'Mã đơn vị', 50], ['unitName', 'Tên đơn vị', 100]].map(([key, label, maxLength]) => <label key={key}>{label}<input required={key !== 'partnerSKU'} maxLength={maxLength} value={product[key]} onChange={e => setProduct({ ...product, [key]: e.target.value })}/></label>)}<label>Serial type<input type="number" min="0" step="1" required value={product.serialType} onChange={e => setProduct({ ...product, serialType: e.target.value })}/></label><label className="checkbox"><input type="checkbox" checked={product.isExpiryDate} onChange={e => setProduct({ ...product, isExpiryDate: e.target.checked })}/>Theo dõi hạn sử dụng</label></div><div className="form-grid"><label>Danh mục (JSON)<textarea value={categories} onChange={e => setCategories(e.target.value)}/><small>{'Ví dụ: [{"categoryCode":"FOOD","categoryName":"Thực phẩm"}]'}</small></label><label>Đơn vị quy đổi (JSON)<textarea value={units} onChange={e => setUnits(e.target.value)}/><small>{'Ví dụ: [{"unitCode":"BOX","unitName":"Hộp","baseUnitQty":10,"isBaseUnit":false}]'}</small></label></div><button className="primary" type="submit">{saving ? 'Đang lưu…' : 'Lưu sản phẩm'}</button></fieldset></form>}
    <section className="panel"><form className="filters" onSubmit={e => { e.preventDefault(); setApplied({ ...filters }); setPage(0); }}>{[['Keyword', 'Tìm tên hoặc SKU'], ['SKUs', 'SKU, phân cách bằng dấu phẩy'], ['PartnerSKUs', 'SKU đối tác, phân cách bằng dấu phẩy']].map(([key, label]) => <label key={key}>{label}<input value={filters[key]} onChange={e => setFilters({ ...filters, [key]: e.target.value })}/></label>)}<label>Số dòng<select value={filters.PageSize} onChange={e => setFilters({ ...filters, PageSize: Number(e.target.value) })}>{[10, 25, 50, 100].map(n => <option key={n}>{n}</option>)}</select></label><button type="submit" disabled={loading}>Tìm kiếm</button></form><ProductTable products={products} loading={loading}/><div className="pagination"><span>{pagination ? `${pagination.totalCount} sản phẩm · Trang ${page + 1}/${pagination.totalPages}` : 'Chưa có dữ liệu'}</span><div><button disabled={loading || !pagination?.hasPreviousPage} onClick={() => setPage(p => p - 1)}>← Trước</button><button disabled={loading || !pagination?.hasNextPage} onClick={() => setPage(p => p + 1)}>Sau →</button></div></div></section>
  </>;
}

function UpdatedProducts() {
  const [from, setFrom] = useState(''), [to, setTo] = useState('');
  const [products, setProducts] = useState([]), [loading, setLoading] = useState(false), [error, setError] = useState('');
  async function search(e) {
    e.preventDefault(); setError(''); setProducts([]);
    if (new Date(from) >= new Date(to)) { setError('Thời gian kết thúc phải lớn hơn thời gian bắt đầu.'); return; }
    setLoading(true);
    try { setProducts(await request('inventory', 'product-query-all', { params: { updatedFrom: new Date(from).toISOString(), updatedTo: new Date(to).toISOString() } })); }
    catch (err) { setError(err.message); } finally { setLoading(false); }
  }
  return <><p className="eyebrow">INVENTORY SERVICE</p><h1>Tra cứu cập nhật</h1><p>Lọc sản phẩm theo khoảng thời gian cập nhật. Mốc kết thúc không được tính vào kết quả.</p><Notice error={error}/><section className="panel"><form className="filters" onSubmit={search}><label>Từ thời điểm<input required type="datetime-local" value={from} onChange={e => setFrom(e.target.value)}/></label><label>Đến thời điểm<input required type="datetime-local" value={to} onChange={e => setTo(e.target.value)}/></label><button className="primary" disabled={loading}>Tra cứu</button></form><ProductTable products={products} loading={loading}/></section></>;
}

function Cdm() {
  const [file, setFile] = useState(null), [upload, setUpload] = useState(null);
  const [busy, setBusy] = useState(''), [error, setError] = useState(''), [success, setSuccess] = useState('');
  const [products, setProducts] = useState([]), [polled, setPolled] = useState(false);
  async function submit(e) {
    e.preventDefault(); setError(''); setSuccess(''); setUpload(null);
    if (!file || !file.name.toLowerCase().endsWith('.xlsx')) { setError('Vui lòng chọn file .xlsx.'); return; }
    setBusy('upload');
    try { const form = new FormData(); form.append('file', file); setUpload(await request('cdm', 'upload-excel', { method: 'POST', body: form })); setSuccess('File đã được xếp hàng xử lý.'); }
    catch (err) { setError(err.message); } finally { setBusy(''); }
  }
  async function poll() {
    setBusy('poll'); setError(''); setSuccess(''); setProducts([]); setPolled(false);
    try { const data = await request('cdm', 'product-polling-check'); setProducts(data); setPolled(true); setSuccess(`Đã kiểm tra đồng bộ: ${data.length} bản ghi mới.`); }
    catch (err) { setError(err.message); } finally { setBusy(''); }
  }
  return <><p className="eyebrow">CDM SERVICE</p><h1>Nhập & đồng bộ dữ liệu</h1><p>Nhập sản phẩm từ Excel và kiểm tra dữ liệu thay đổi từ Inventory.</p><Notice error={error} success={success}/><div className="two-columns"><section className="panel"><div className="feature-icon">↑</div><h2>Nhập file Excel</h2><p>Workbook cần có ba sheet: <code>products</code>, <code>categories</code> và <code>product_units</code>. Các sheet liên kết bằng cột <code>sku</code>.</p><form onSubmit={submit}><label className="upload">Chọn file .xlsx<input type="file" accept=".xlsx" disabled={!!busy} onChange={e => { setFile(e.target.files?.[0] || null); setUpload(null); setSuccess(''); }}/></label><button className="primary" disabled={!!busy || !file}>{busy === 'upload' ? 'Đang tải…' : 'Tải lên & xử lý'}</button></form>{upload && <div className="receipt"><strong>Đã xếp hàng</strong><p>Mã tác vụ: <code>{upload.taskId}</code></p><p>File: <code>{upload.fileName}</code></p><small>API hiện chưa hỗ trợ xem tiến độ hoặc kết quả tác vụ.</small></div>}</section><section className="panel"><div className="feature-icon">↻</div><h2>Kiểm tra đồng bộ</h2><p>Lấy dữ liệu thay đổi từ Inventory và lưu các bản ghi mới vào CDM. Khoảng thời gian do backend quyết định.</p><button disabled={!!busy} onClick={poll}>{busy === 'poll' ? 'Đang đồng bộ…' : 'Chạy kiểm tra đồng bộ'}</button><p className="hint">Thao tác này ghi dữ liệu vào CDM; kết quả hiển thị các bản ghi được tạo mới trong lần chạy.</p></section></div>{polled && <section className="panel"><h2>Kết quả đồng bộ · {products.length} bản ghi mới</h2><ProductTable products={products} loading={false}/></section>}</>;
}

function Health() {
  const [results, setResults] = useState({}), [busy, setBusy] = useState(false);
  async function check() {
    setBusy(true);
    await Promise.all(['inventory', 'cdm'].map(async service => {
      try { const data = await request(service, 'health-check'); setResults(r => ({ ...r, [service]: { data } })); }
      catch (err) { setResults(r => ({ ...r, [service]: { error: err.message } })); }
    }));
    setBusy(false);
  }
  return <><div className="section-head"><div><p className="eyebrow">HỆ THỐNG</p><h1>Trạng thái service</h1><p>Kiểm tra kết nối cơ sở dữ liệu và cache.</p></div><button className="primary" onClick={check} disabled={busy}>{busy ? 'Đang kiểm tra…' : 'Kiểm tra kết nối'}</button></div><div className="two-columns">{['inventory', 'cdm'].map(service => <section className="panel" key={service}><h2>{service === 'inventory' ? 'Inventory Service' : 'CDM Service'}</h2>{busy ? <p>Đang kiểm tra…</p> : results[service]?.error ? <Notice error={results[service].error}/> : results[service]?.data ? <dl>{Object.entries(results[service].data).map(([key, value]) => <div key={key}><dt>{key}</dt><dd>{String(value)}</dd></div>)}</dl> : <p>Chưa kiểm tra kết nối.</p>}</section>)}</div></>;
}

const tabs = [['inventory', '▦', 'Sản phẩm'], ['updates', '◷', 'Tra cứu cập nhật'], ['cdm', '⇄', 'Nhập & đồng bộ'], ['health', '◉', 'Trạng thái service']];
function App() {
  const [tab, setTab] = useState('inventory');
  return <div className="layout"><aside><a className="brand" href="/">K<span>SynerX</span><small>DATA WORKSPACE</small></a><div className="nav-label">KHÔNG GIAN LÀM VIỆC</div><nav aria-label="Điều hướng chính">{tabs.map(([id, icon, name]) => <button key={id} className={tab === id ? 'active' : ''} aria-current={tab === id ? 'page' : undefined} onClick={() => setTab(id)}><span>{icon}</span>{name}</button>)}</nav><div className="sidebar-footer"><span className="dot"/> Inventory + CDM<small>Quản lý dữ liệu sản phẩm</small></div></aside><div className="workspace"><header><span>Workspace <b>/ {tabs.find(t => t[0] === tab)[2]}</b></span><span className="avatar">K</span></header><main>{tab === 'inventory' ? <Inventory/> : tab === 'updates' ? <UpdatedProducts/> : tab === 'cdm' ? <Cdm/> : <Health/>}</main><footer>KSynerX · Product data management</footer></div></div>;
}

createRoot(document.getElementById('root')).render(<React.StrictMode><App/></React.StrictMode>);
