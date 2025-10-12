// 配置lazysizes
// window.lazySizesConfig = window.lazySizesConfig || {};
// window.lazySizesConfig.loadMode = 1; // 逐个加载模式
// window.lazySizesConfig.addClasses = true;
// window.lazySizesConfig.expFactor = 1.5; // 提前加载的距离倍数
// window.lazySizesConfig.throttleDelay = 100; // 节流延迟时间

let tips = null;
let login = null;

async function openPlayPage() {
	// <a class="play-btn no-long-press" href="javascript:void(0)" data-url="{{ url_for('media.play_page', mid=movie.uuid) }}?typ={{ movie.typ }}" title="" aria-label="播放页面">
	const movieItems = document.getElementById('movieItems');
	movieItems.addEventListener('click', async (event) => {
		event.preventDefault();
		const button = event.target.closest('.play-btn');
		if (!button) return;
		const url = button.getAttribute('data-url');
		if (!url) return;
		login.show();
	});
}

async function submitWish(wishInput, wishBtn) {
	const inputValue = wishInput.value.trim();
	if (inputValue === '' || inputValue === null || /^\d+$/.test(inputValue) || inputValue.length > 100) {
		wishInput.value = '';
		wishInput.focus();
		wishInput.placeholder = '说点儿啥？';
		return;
	}
	wishBtn.disabled = true;

	const logged = await login.waitForLogin();
	if (!logged) {
		wishBtn.disabled = false;
		return;
	}

	hideNavbar();
	if (backToTop) {
		backToTop.click();
	}

	tips.show('提交中...', true, false);

	try {
		const res = await apiClient.post('/api/wish', {
			content: inputValue
		});
		if (res.data?.code === 200) {
			tips.show(res.data?.msg || '已发送', true, true, 2000);
		} else {
			tips.show('已发送,感觉没有提交成功。', true, true, 2000);
		}
		wishInput.value = '';
		wishInput.placeholder = '想看点啥？';
	} catch (error) {
		const err = apiClient.handleError(error);
		tips.show(err, true, true, 2500);
	} finally {
		tips.hideLoading();
		wishBtn.disabled = false;
	}
}

document.addEventListener('click', function (event) {
	const collapses = document.querySelectorAll('.collapse.show');
	collapses.forEach(collapse => {
		if (!collapse.contains(event.target)) {
			const collapseInstance = bootstrap.Collapse.getInstance(collapse);
			if (collapseInstance) {
				collapseInstance.hide();
			}
		}
	});
});

document.addEventListener('lazyloaded', function (e) {
	const img = e.target;
	if (img.classList.contains('poster-img')) {
		if (img.naturalHeight > img.naturalWidth) {
			img.classList.add('portrait');
		}
	}
});

// lazysizes.js处理图片加载错误 | hide the image element when the image load error
document.addEventListener('lazybeforeunveil', function (e) {
	e.target.onerror = function () {
		this.style.display = 'none';
	};
});

document.addEventListener('DOMContentLoaded', function () {

	tips = new ToastManager('tip-toast', 'tip-loading', 'tip-content');

	login = new LoginManager();

	const wishBtn = document.getElementById('bucket-list-btn');
	const wishInput = document.getElementById('bucket-list-input');
	wishBtn.addEventListener('click', function (e) {
		e.preventDefault();
		debounce(submitWish(wishInput, e.currentTarget), 200);
	});

	login.setOnHideCallback(() => {
		wishBtn.disabled = false;
	});

	// openPlayPage();

	// 滚轮滑动时禁止鼠标指针事件,减少绘制体验感差点儿。
	// let isZoomed = false;
	// document.querySelectorAll('.movie-item-zoom').forEach(item => {
	// 	item.addEventListener('mouseenter', () => {
	// 		isZoomed = true;
	// 	});
	// 	item.addEventListener('mouseleave', () => {
	// 		isZoomed = false;
	// 	});
	// });
	// window.addEventListener('wheel', function(e) {
	// 	if (isZoomed) {
	// 		e.preventDefault();
	// 	}
	// }, { passive: false });
});



