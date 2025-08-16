// Content script placeholder: extracts text from the page
const bodyText = document.body ? document.body.innerText : '';
console.log('AI Auditor content script loaded, text length:', bodyText.length);
// Export for testability
export const extractedText = bodyText;



