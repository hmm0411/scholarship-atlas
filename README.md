# Scholarship Atlas 2027 — cập nhật trực tiếp repository cũ

Bản này là **toàn bộ source**, được thiết kế để CHÉP ĐÈ vào chính repo GitHub Pages hiện tại, không cần tạo repo khác. Các thay đổi người dùng lưu trên trình duyệt cũ nên hãy **Export JSON một lần làm bản sao lưu trước khi thay code**, dù về sau sử dụng cloud sync không cần upload JSON thủ công.

## VS Code / PowerShell

```powershell
git clone https://github.com/USERNAME/REPO_CU.git
cd REPO_CU
code .
```

Giải nén ZIP này, sao chép toàn bộ file **kể cả thư mục `.github` ẩn** vào đúng thư mục repo đang mở, đồng ý Replace khi được hỏi. Đảm bảo `index.html`, `config.js`, `data/`, `scripts/`, `supabase/`, `.github/` nằm **ngay gốc repo**, không lồng thêm thư mục con.

```powershell
python -m unittest discover -s scripts -p 'test_*.py' -v
python scripts/check_sources.py
python -m http.server 5500
```

Truy cập `http://localhost:5500/`. Khi kiểm tra xong:

```powershell
git status
git add .
git commit -m "feat: scholarship cloud dashboard and expanded official source monitoring"
git push origin main
```

Nếu branch mặc định là `master`, dùng `git push origin master`. GitHub → Settings → Pages → Deploy from a branch → main (hoặc master) → /(root).

## Nguồn giám sát và độ tin cậy

- Có **28 nguồn** trong `data/sources.json` ở 9 vùng/quốc gia; gồm Oxford Optiver & ACS, Gates Cambridge, British Council, Vingroup, VinUni, NTU, NUS, SMU, AI Singapore, A*STAR, HKPFS, SEU, CSC, Tsinghua, ZJU, KAIST, GKS, MEXT, JASSO, Erasmus Mundus, DAAD, v.v.
- Danh sách là **URL ứng viên để giám sát**, không có nghĩa từng URL xác nhận học bổng 2027 hay tất cả nguồn luôn truy cập được. Một số là cổng chung, cần thêm URL chương trình cụ thể sau khi được công bố.
- `scripts/check_sources.py` đọc config, kiểm tra HTML mỗi ngày, lưu báo cáo ở `data/updates.json` và baseline hash ở `data/source_state.json`. Nguồn không đọc được báo lỗi thay vì bịa thông tin.
- Lần đầu chỉ tạo baseline; các lần sau phát hiện thay đổi. **Không tự ghi đè deadline hay eligibility**: đổi nội dung trang là tín hiệu cần kiểm tra, không phải ngày chính thức.
- Trong GitHub → Actions → Monitor official scholarship sources → Run workflow để chạy ngay; lịch chạy mỗi ngày khoảng 09:17 Việt Nam nhưng có thể trễ. Repo phải cho phép GitHub Actions push bằng `GITHUB_TOKEN` (Settings → Actions → General → Workflow permissions → Read and write).
- Muốn thêm nguồn, thêm một object `id, name, region, organization, url, priority, enabled` vào `data/sources.json`; không cần sửa Python.
- Tôn trọng robots.txt, điều khoản, giới hạn tốc độ website; không bảo đảm nội dung JavaScript hoặc PDF/hình ảnh được trích xuất chính xác.

## Đồng bộ dữ liệu và trợ lý AI


1. Tạo project Supabase tại https://supabase.com/dashboard.
2. SQL Editor → chạy `supabase/schema.sql` để tạo bảng và RLS.
3. Project Settings / API → lấy **Project URL** và **publishable/anon key**. Sửa `config.js` và điền 2 giá trị. Public anon/publishable key được phép có ở frontend **chỉ khi RLS bật**. Không đưa `service_role` key vào repo.
4. Authentication → Providers → Email, bật email auth và cân nhắc **Confirm email**. URL Configuration → Site URL & Redirect URLs: thêm URL GitHub Pages của bạn.
5. Commit `config.js` lên repository. Mở web → **Đồng bộ & Tin mới** → Đăng ký/Đăng nhập. Bản dữ liệu trình duyệt đầu tiên sẽ được đẩy lên account nếu cloud trống; nếu account đã có bản cloud thì tải bản đó.
6. Chỉnh sửa học bổng/công việc → auto sync sau khoảng 1.2 giây. Có thể kiểm tra bảng `user_workspaces` trong Supabase. Khi đổi thiết bị, đăng nhập cùng email.

**Chú ý:** Dữ liệu người dùng lưu riêng theo RLS. Khi đăng xuất, dữ liệu local vẫn còn trong cùng trình duyệt. Không nên dùng thiết bị công cộng; xóa dữ liệu local bằng giao diện/trình duyệt khi cần. Đồng bộ bản toàn bộ workspace theo last-write-wins; nếu mở 2 thiết bị sửa đồng thời có thể ghi đè, nên tránh chỉnh sửa song song. Nên xuất bản sao lưu định kỳ.



- Phần trợ lý offline cũ luôn hoạt động. AI trực tuyến yêu cầu Supabase + Edge Function + API key đặt **phía server**.
- Cài Supabase CLI, đăng nhập: `supabase login`, rồi `supabase link --project-ref YOUR_PROJECT_REF`.
- Đặt secret: `supabase secrets set OPENAI_API_KEY=YOUR_API_KEY` (qua terminal riêng, không commit vào git). Có thể thêm `OPENAI_MODEL=gpt-4.1-mini`.
- Deploy: `supabase functions deploy assistant`.
- Supabase Functions authentication/JWT verification: giữ bật xác thực JWT (hoặc nếu cấu hình API mới yêu cầu tắt gateway verification, function vẫn tự kiểm tra `auth.getUser`, nhưng nên giữ gateway auth). Trình duyệt phải có session Supabase.
- Vào **Đồng bộ & Tin mới** → đặt câu hỏi → **Hỏi AI online**.
- Function có kiểm tra người dùng và đọc bản ghi của người đó từ bảng được bảo vệ RLS; không dùng internet để xác minh học bổng mới. Cân nhắc quota/rate limit và ngân sách nếu web công khai, vì người đăng nhập có thể gọi function nhiều lần.


## Giới hạn

- GitHub Pages là hosting tĩnh; GitHub Actions chỉ cập nhật feed public, Supabase mới đồng bộ dữ liệu cá nhân.
- Không push công khai giấy tờ, thông tin hồ sơ riêng, file .env, OpenAI API key hoặc service_role key.
- Website AI trả lời từ dữ liệu lưu; không tự duyệt web theo thời gian thực.
- Nếu clone repo cũ mà chỉ thay tệp, cần chắc chắn đã backup localStorage trước khi thay đổi cấu trúc dữ liệu.
