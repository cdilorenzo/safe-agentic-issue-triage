const input = $('Validate URL + Demo Fixtures').item.json;
return {json:{...input,input_ok:false,processing_outcome:'failed_closed_github_fetch_error',
  validation_errors:'Public GitHub GET failed (private/missing issue, network problem or API rate limit)'}};
