export class ApiService {
    static async sendMergeRequest(formData, base_url) {
        const response = await fetch(
            `${base_url}`, {
                method: 'POST',
                body: formData,
            }
        )
        if (response.ok) {
            return response.json()
        }
    }
}