var assert  = require('assert');

const url       = '$uri/api/v1/ping/all',
      test_url  = 'https://' + $secure.PROD_API_TEST_CLIENT_ID + ':' + $secure.PROD_API_TEST_CLIENT_SECRET + '@' + url, 
      headers   = {
                    'Content-Type'    : 'application/json',
                    'Accept'          : 'application/json',
                    'Content-Length'  : 0
                  }

var runTest = function(){
  let test_opts = {
    url: test_url, 
    headers: headers
  }
  $http.get(test_opts, function(err, resp, body){
    assert.equal(resp.statusCode, 200, 'Expected a 200 OK response');
  });
}

runTest();
