const currentHost = window.location.hostname;
const isLocalHost = ["localhost", "127.0.0.1", "0.0.0.0"].includes(currentHost);
const forwardedApiHost = currentHost.replace("-5500.", "-8000.");

window.BDIA_API_URL = window.BDIA_API_URL || (
	isLocalHost
		? `${window.location.protocol}//${currentHost}:8000`
		: `${window.location.protocol}//${forwardedApiHost}`
);
