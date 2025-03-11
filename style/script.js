document.getElementById("styleTransferForm").addEventListener("submit", async (e) => {
    e.preventDefault();

    const contentImage = document.getElementById("contentImage").files[0];
    const styleImage = document.getElementById("styleImage").files[0];

    if (!contentImage || !styleImage) {
        alert("Please upload both content and style images!");
        return;
    }

    const formData = new FormData();
    formData.append("content_image", contentImage);
    formData.append("style_image", styleImage);

    try {
        const response = await fetch("http://localhost:5000/style-transfer", {
            method: "POST",
            body: formData,
        });

        if (!response.ok) {
            throw new Error("Style transfer failed!");
        }

        const result = await response.json();
        document.getElementById("stylizedImage").src = result.image_url;
        document.getElementById("stylizedImage").style.display = "block";
        document.getElementById("message").textContent = result.message;
    } catch (error) {
        console.error(error);
        alert("An error occurred. Please try again.");
    }
});