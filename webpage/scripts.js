async function selectImage() {  
  const photoField = fileSelect.files[0];
  const dataUri = await dataUriFromFormField(photoField);
  
  const fullImage = document.createElement('img');
  fullImage.addEventListener('load', () => {
    const resizedDataUri = resizeImage(fullImage, 380);
    document.querySelector('#img-preview').src = resizedDataUri;
    base64String = resizedDataUri.replace("data:", "").replace(/^.+,/, "");
    uploadFile(base64String)
  });
  fullImage.src = dataUri;
}

function dataUriFromFormField (field) {
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.addEventListener('load', () => {
      resolve(reader.result);
    });
    reader.readAsDataURL(field);
  });
}

function resizeImage (fullImage, wantedWidth) {
  const canvas = document.createElement('canvas');
  const ctx = canvas.getContext('2d');
  const aspect = fullImage.width / fullImage.height;

  canvas.width = wantedWidth;
  canvas.height = wantedWidth / aspect;

  ctx.drawImage(fullImage, 0, 0, canvas.width, canvas.height);
  return canvas.toDataURL();
}

async function uploadFile(file) {
  clearResults();
  var $alert = $('.alert');
  let formData = new FormData();
  formData.append("filename", 'image')
  formData.append("filedata", file)

  $.ajax('https://xxlkbgor75nvr7qw256z2xnrdm0ppqai.lambda-url.us-east-2.on.aws/image', {
      method: 'POST',
      data: formData,
      processData: false,
      contentType: false,
              
      success: function (data) {
          $alert.hide();
          document.getElementById('result').innerHTML = data.category
          updateTable(data.confs)
          },
      error: function () {
          $alert.show();
          }
  });
}

function clearResults () {
  var table = document.getElementById("table");
  $("#table").find("tr:not(:first)").remove();
  document.getElementById('result').innerHTML = 'Loading results...';
}

function updateTable(object){
  var table = document.getElementById("table");
  $("#table").find("tr:not(:first)").remove();

  var count = 1
  for(property in object){
    var row = table.insertRow();
    var pos = row.insertCell(0);
    var name = row.insertCell(1);
    var conf = row.insertCell(2);

    pos.innerHTML = count++;
    name.innerHTML = `${object[property].name}`;
    conf.innerHTML = `${object[property].conf}%`;
  }
}