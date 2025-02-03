function copyToClipboard(button) {
    const text = button.getAttribute("data-text");

    navigator.clipboard.writeText(text).then(function() {
        const alertBox = document.createElement("span");
        alertBox.className = "text-success ms-2";
        alertBox.innerText = "Copied!";
        
        button.parentElement.appendChild(alertBox);
        setTimeout(() => alertBox.remove(), 2000);
    }).catch(err => console.error('Copy failed:', err));
}