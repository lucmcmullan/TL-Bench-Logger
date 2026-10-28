window.addEventListener("pageshow", function (event) {
    if (event.persisted) {
        this.location.reload()
    }
})