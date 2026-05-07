function copyToClipboard(button) {
    const text = button.getAttribute("data-text");

    navigator.clipboard.writeText(text);
}