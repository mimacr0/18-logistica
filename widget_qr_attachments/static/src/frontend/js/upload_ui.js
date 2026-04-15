(function() {
    'use strict';

    // Get token from odoo config or from URL query params as fallback
    function getToken() {
        if (typeof odoo !== 'undefined' && odoo.token) return odoo.token;
        const params = new URLSearchParams(window.location.search);
        return params.get('token') || '';
    }

    let attachmentList, noAttachments, fileInput, cameraInput;

    function init() {
        attachmentList = document.getElementById('attachment_list');
        noAttachments = document.getElementById('no_attachments');
        fileInput = document.getElementById('file_input');
        cameraInput = document.getElementById('camera_input');

        if (fileInput) fileInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });
        if (cameraInput) cameraInput.addEventListener('change', (e) => {
            handleFiles(e.target.files);
        });

        // Initial fetch
        fetchAttachments();
    }

    // Helper for JSON-RPC
    async function jsonRpc(url, params) {
        const response = await fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': odoo.csrf_token,
            },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: params,
                id: Math.floor(Math.random() * 1000 * 1000),
            }),
        });
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error.data ? data.error.data.message : data.error.message);
        }
        return data.result;
    }

    function createAttachmentItem(attachment) {
        const div = document.createElement('div');
        div.className = 'attachment-item list-group-item';
        div.id = 'attachment-' + attachment.id;

        let previewHtml = '';
        if (attachment.is_image) {
            previewHtml = `<img src="${attachment.thumbnail_url}" class="attachment-preview" alt="preview"/>`;
        } else {
            previewHtml = `<div class="attachment-preview"><i class="fa fa-file"></i></div>`;
        }

        div.innerHTML = `
            ${previewHtml}
            <div class="attachment-info">
                <span class="attachment-name">${attachment.name}</span>
                <span class="attachment-size">${attachment.mimetype}</span>
            </div>
            <button class="btn btn-delete" data-id="${attachment.id}">
                <i class="fa fa-trash-o"></i>
            </button>
        `;

        div.querySelector('.btn-delete').addEventListener('click', async (e) => {
            if (confirm('Are you sure you want to delete this file?')) {
                try {
                    await jsonRpc('/qr_upload/delete_attachment', {
                        attachment_id: attachment.id,
                        model: odoo.model,
                        res_id: odoo.res_id,
                        token: getToken(),
                    });
                    div.remove();
                    if (attachmentList && attachmentList.children.length === 0) {
                        noAttachments.classList.remove('d-none');
                    }
                } catch (err) {
                    alert('Delete error: ' + err.message);
                }
            }
        });

        return div;
    }

    async function fetchAttachments() {
        if (!attachmentList) return;
        try {
            const result = await jsonRpc('/qr_upload/get_attachments', {
                model: odoo.model,
                res_id: odoo.res_id,
                token: getToken(),
            });
            attachmentList.innerHTML = '';
            if (result.length > 0) {
                if (noAttachments) noAttachments.classList.add('d-none');
                for(const attachment of result) {
                    attachmentList.appendChild(createAttachmentItem(attachment));
                }
            } else {
                if (noAttachments) noAttachments.classList.remove('d-none');
            }
        } catch (err) {
            console.error('Error fetching attachments:', err);
        }
    }

    async function handleFiles(files) {
        if (!files || files.length === 0) return;
        showLoading(true);
        for(const file of files) {
            try {
                const reader = new FileReader();
                const contentPromise = new Promise((resolve) => {
                    reader.onload = (e) => resolve(e.target.result.split(',')[1]);
                });
                reader.readAsDataURL(file);
                const content = await contentPromise;

                const result = await jsonRpc('/qr_upload/upload_file', {
                    model: odoo.model,
                    res_id: odoo.res_id,
                    name: file.name,
                    content: content,
                    mimetype: file.type,
                    token: getToken(),
                });

                if (result.success) {
                    await fetchAttachments();
                } else {
                    alert('Error uploading ' + file.name + ': ' + result.error);
                }
            } catch (err) {
                alert('Error uploading ' + file.name + ': ' + err.message);
            }
        }
        showLoading(false);
        // Reset inputs to allow uploading the same file again
        if (fileInput) fileInput.value = '';
        if (cameraInput) cameraInput.value = '';
    }

    function showLoading(show) {
        if (show) {
            if (!document.getElementById('loading_overlay')) {
                const overlay = document.createElement('div');
                overlay.id = 'loading_overlay';
                overlay.innerHTML = `
                    <div class="spinner-border text-primary mb-3" role="status" style="width: 3rem; height: 3rem;"></div>
                    <span class="fw-bold text-primary">Uploading...</span>
                `;
                document.body.appendChild(overlay);
            }
        } else {
            const overlay = document.getElementById('loading_overlay');
            if (overlay) overlay.remove();
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }

})();
