export class ApiService {
    static async sendMergeRequest(formData) {
        const response = await fetch(
            '/merge-files', {
                method: 'POST',
                body: formData,
            }
        )
        if (response.ok) {
            return response.json()
        }
    }
}